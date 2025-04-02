from flask import Flask, jsonify, request
import sqlite3
import schedule
import time
import threading
import logging
import os
import subprocess
import json
import tempfile
from datetime import datetime, timedelta
from config import DB_NAME, BACKEND_API_SEND_DATA, BACKEND_API_SEND_CURRENT, RETRY_ATTEMPTS, BASE_DELAY

# Set logging to only log errors and successes.
logging.basicConfig(filename="api_log.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# Global variable to track last sent timestamp (used for on-demand sending)
LAST_SENT_TIMESTAMP = None

def fetch_recent_data(after=None):
    """
    Fetch records from the database.
    If 'after' is provided, fetch records with timestamp > after,
    otherwise fetch records from the last hour.
    Only include fields that the backend expects (omitting the primary key).
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if after:
            cursor.execute("""
                SELECT timestamp, sensor_id, adc_value, moisture_level, digital_status,
                       weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
                       location, weather_fetched, device_id
                FROM moisture_data
                WHERE timestamp > ?
            """, (after,))
        else:
            lower_bound = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                SELECT timestamp, sensor_id, adc_value, moisture_level, digital_status,
                       weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
                       location, weather_fetched, device_id
                FROM moisture_data
                WHERE timestamp > ?
            """, (lower_bound,))
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database connection/query error: {e}")
        return []
    finally:
        conn.close()

    # Build records without the 'id' field.
    records = []
    for row in rows:
        record = {
            "timestamp": row[0],
            "sensor_id": row[1],
            "adc_value": row[2],
            "moisture_level": round(row[3], 2),
            "digital_status": row[4],
            "weather_temp": row[5],
            "weather_humidity": row[6],
            "weather_sunlight": row[7],
            "weather_wind_speed": row[8],
            "location": row[9],
            "weather_fetched": row[10],
            "device_id": row[11]
        }
        records.append(record)
    return records

def send_request_curl(url, data):
    """
    Write the JSON payload (with key "data") to a temporary file
    and use curl to send it. Returns (True, output) on success.
    """
    payload = json.dumps({"data": data})
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write(payload)
        tmp_filename = tmp.name
    command = [
        "curl",
        "--location",
        "--silent",
        "--show-error",
        "--header", "Content-Type: application/json",
        "--data-binary", f"@{tmp_filename}",
        "--write-out", "%{http_code}",
        url
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    os.remove(tmp_filename)
    if result.returncode == 0:
        output = result.stdout.strip()
        http_code = output[-3:]
        if http_code == "200":
            logging.error("Data sent successfully.")
            return True, output
        else:
            logging.error(f"Curl command returned HTTP code {http_code}: {output}")
            return False, output
    else:
        logging.error(f"Curl command failed: {result.stderr}")
        return False, result.stderr

def retry_with_backoff(func, max_attempts=RETRY_ATTEMPTS, base_delay=BASE_DELAY):
    for attempt in range(max_attempts):
        if func():
            return True
        delay = base_delay * (2 ** attempt)
        logging.error(f"Retrying after {delay} seconds...")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False

def send_data_to_backend(url, after=None):
    """
    Fetch data from DB (after a given timestamp if provided) and send it to the backend using curl.
    """
    effective_after = after if after else (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    data = fetch_recent_data(after=effective_after)
    if not data:
        logging.error("No new data to send.")
        return True, None  # Consider no data as success.
    def send_request():
        success, _ = send_request_curl(url, data)
        return success
    success = retry_with_backoff(send_request)
    return success, data if success else None

@app.route("/send-current", methods=["POST"])
def send_current_data():
    """
    Endpoint to send data (for on-demand requests) using the send-current API.
    Data is fetched from DB after LAST_SENT_TIMESTAMP.
    """
    global LAST_SENT_TIMESTAMP
    success, data = send_data_to_backend(BACKEND_API_SEND_CURRENT, after=LAST_SENT_TIMESTAMP)
    if data:
        try:
            LAST_SENT_TIMESTAMP = max(record["timestamp"] for record in data)
        except Exception as e:
            logging.error(f"Error updating LAST_SENT_TIMESTAMP: {e}")
    if success:
        return jsonify({"message": "Current data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

@app.route("/manual", methods=["POST"])
def send_manual_data():
    """
    Manual endpoint to send data from the DB after a provided 'after' timestamp.
    Expects JSON input with the key 'after'.
    """
    global LAST_SENT_TIMESTAMP
    req_json = request.get_json() or {}
    after_timestamp = req_json.get("after")
    if not after_timestamp:
        return jsonify({"message": "Missing 'after' timestamp in request"}), 400
    success, data = send_data_to_backend(BACKEND_API_SEND_DATA, after=after_timestamp)
    if data:
        try:
            LAST_SENT_TIMESTAMP = max(record["timestamp"] for record in data)
        except Exception as e:
            logging.error(f"Error updating LAST_SENT_TIMESTAMP: {e}")
    if success:
        return jsonify({"message": "Manual data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send manual data"}), 500

@app.route("/send-data", methods=["POST"])
def send_auto_data():
    """
    Endpoint for auto-sending data (e.g. when triggered by a scheduler).
    Data is fetched from the last hour.
    """
    global LAST_SENT_TIMESTAMP
    success, data = send_data_to_backend(BACKEND_API_SEND_DATA)
    if data:
        try:
            LAST_SENT_TIMESTAMP = max(record["timestamp"] for record in data)
        except Exception as e:
            logging.error(f"Error updating LAST_SENT_TIMESTAMP: {e}")
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

def scheduled_job():
    # Auto-send data every hour using the BACKEND_API_SEND_DATA endpoint.
    send_data_to_backend(BACKEND_API_SEND_DATA)

def schedule_data_sending():
    schedule.every(1).hours.do(scheduled_job)
    logging.error("Scheduled job registered successfully.")
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_schedule_in_thread():
    thread = threading.Thread(target=schedule_data_sending)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    run_schedule_in_thread()
    app.run(host="0.0.0.0", port=5001, debug=False)
