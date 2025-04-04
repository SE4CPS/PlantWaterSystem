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

# Configure logging: log only errors and key success messages.
logging.basicConfig(filename="api_log.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# Global variable to track the last successfully sent timestamp (as a string "YYYY-MM-DD HH:MM:SS")
LAST_SENT_TIMESTAMP = None

def fetch_recent_data(after=None):
    """
    Fetch records from the local DB.
    If 'after' is provided, fetch records with timestamp > after;
    otherwise, fetch records from the past hour.

    IMPORTANT: The query column names must exactly match the names in the NeonDB table.
    Here we assume that the database columns are named:
      - timestamp
      - sensorid
      - adcvalue
      - moisturelevel
      - digitalstatus
      - weathertemp
      - weatherhumidity
      - weathersunlight
      - weatherwindspeed
      - location
      - weatherfetched
      - device_id
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if after:
            query = """
                SELECT timestamp, sensorid, adcvalue, moisturelevel, digitalstatus,
                       weathertemp, weatherhumidity, weathersunlight, weatherwindspeed,
                       location, weatherfetched, device_id
                FROM moisture_data
                WHERE timestamp > ?
            """
            cursor.execute(query, (after,))
        else:
            lower_bound = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            query = """
                SELECT timestamp, sensorid, adcvalue, moisturelevel, digitalstatus,
                       weathertemp, weatherhumidity, weathersunlight, weatherwindspeed,
                       location, weatherfetched, device_id
                FROM moisture_data
                WHERE timestamp > ?
            """
            cursor.execute(query, (lower_bound,))
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database connection/query error: {e}")
        return []
    finally:
        conn.close()

    records = []
    for row in rows:
        record = {
            "timestamp": row[0],
            "sensor_id": row[1],            # now coming from column 'sensorid'
            "adc_value": row[2],            # coming from 'adcvalue'
            "moisture_level": round(row[3], 2),  # 'moisturelevel'
            "digital_status": row[4],       # 'digitalstatus'
            "weather_temp": row[5],         # 'weathertemp'
            "weather_humidity": row[6],     # 'weatherhumidity'
            "weather_sunlight": row[7],     # 'weathersunlight'
            "weather_wind_speed": row[8],   # 'weatherwindspeed'
            "location": row[9],
            "weather_fetched": row[10],     # 'weatherfetched'
            "device_id": row[11]
        }
        records.append(record)
    return records

def send_request_curl(url, data):
    """
    Write the JSON payload (wrapped in key "data") to a temporary file and use curl to send it.
    If the HTTP response is 200 or the output contains an error message indicating a duplicate key
    or "connection already closed", we treat the send as successful.
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
        elif ("duplicate key value violates unique constraint" in output or
              "connection already closed" in output):
            logging.error("Duplicate or connection closed error encountered; treating as success.")
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
    Determine the effective 'after' timestamp (the later of the provided timestamp and LAST_SENT_TIMESTAMP),
    fetch data from the DB, and send it via curl.
    """
    global LAST_SENT_TIMESTAMP
    try:
        provided_dt = datetime.strptime(after, "%Y-%m-%d %H:%M:%S") if after else datetime.now() - timedelta(hours=1)
    except Exception:
        provided_dt = datetime.now() - timedelta(hours=1)

    if LAST_SENT_TIMESTAMP:
        try:
            last_sent_dt = datetime.strptime(LAST_SENT_TIMESTAMP, "%Y-%m-%d %H:%M:%S")
        except Exception:
            last_sent_dt = provided_dt
        effective_dt = max(provided_dt, last_sent_dt)
    else:
        effective_dt = provided_dt

    effective_after = effective_dt.strftime("%Y-%m-%d %H:%M:%S")
    data = fetch_recent_data(after=effective_after)
    if not data:
        logging.error("No new data to send.")
        return True, None  # No data is considered success.
    def send_request():
        success, _ = send_request_curl(url, data)
        return success
    success = retry_with_backoff(send_request)
    return success, data if success else None

@app.route("/send-current", methods=["POST"])
def send_current_data():
    """
    Endpoint to send on-demand data using the BACKEND_API_SEND_CURRENT endpoint.
    Data is fetched after LAST_SENT_TIMESTAMP.
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
    Manual endpoint to send data after a user-provided 'after' timestamp.
    Expects a JSON payload with an "after" key. Uses BACKEND_API_SEND_DATA.
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
    Endpoint for auto-sending data (e.g. triggered by a scheduler).
    Data is fetched from the past hour (or after LAST_SENT_TIMESTAMP if set).
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
