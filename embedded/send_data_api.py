import os
import sqlite3
import time
import threading
import logging
<<<<<<< HEAD
import schedule
import subprocess
import json
from datetime import datetime
from flask import Flask, jsonify, request
from config import (
    DB_NAME,
    BACKEND_API_SEND_DATA,
    BACKEND_API_SEND_CURRENT,
    SENSOR_READ_INTERVAL,
    RETRY_ATTEMPTS,
    BASE_DELAY,
)

# Configure logging
logging.basicConfig(
    filename="api_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
=======
import os
from datetime import datetime, timedelta
from config import DB_NAME, BACKEND_API_URL, RETRY_ATTEMPTS, BASE_DELAY

logging.basicConfig(filename="api_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
>>>>>>> origin/main

app = Flask(__name__)
LAST_SENT_TIMESTAMP = None  # Tracks the last sent record's timestamp

<<<<<<< HEAD
# File to persist the last successfully sent row ID
LAST_SENT_FILE = "last_sent_id.txt"

def load_last_sent_id():
    """Load the last sent ID from persistent storage."""
    if os.path.exists(LAST_SENT_FILE):
        try:
            with open(LAST_SENT_FILE, "r") as f:
                return int(f.read().strip())
        except Exception as e:
            logging.error(f"Error loading LAST_SENT_ID: {e}")
    return 0

def save_last_sent_id(last_id):
    """Persist the last sent ID so it survives a restart."""
    try:
        with open(LAST_SENT_FILE, "w") as f:
            f.write(str(last_id))
    except Exception as e:
        logging.error(f"Error saving LAST_SENT_ID: {e}")

# Global variable for the last sent row id, persistent across restarts.
LAST_SENT_ID = load_last_sent_id()

def fetch_all_unsent_rows(last_id):
    """
    Fetch all rows (readings) from the database with id greater than last_id.
    Returns a list of rows (each as a tuple).
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
                   weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
                   location, weather_fetched, device_id
            FROM moisture_data
            WHERE id > ?
            ORDER BY id ASC
            """,
            (last_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logging.error(f"Database error in fetch_all_unsent_rows: {e}")
        return []

def row_to_dict(row):
    """
    Convert a database row to a dictionary matching the required JSON structure.
    """
    return {
        "id": row[0],
        "timestamp": row[1],
        "sensor_id": row[2],
        "adc_value": row[3],
        "moisture_level": round(row[4], 2) if row[4] is not None else 0,
        "digital_status": row[5] or "",
        "weather_temp": row[6] or 0,
        "weather_humidity": row[7] or 0,
        "weather_sunlight": row[8] or 0,
        "weather_wind_speed": row[9] or 0,
        "location": row[10] or "",
        "weather_fetched": row[11] or "",
        "device_id": row[12] or "",
    }

def send_unsent_rows_via_curl(url, batch_size=20):
    """
    Fetch all unsent rows, split into batches, serialize each batch to JSON and
    send via curl. Only mark as sent when HTTP 200 is returned.
    """
    global LAST_SENT_ID
    rows = fetch_all_unsent_rows(LAST_SENT_ID)
    if not rows:
        logging.info("No unsent rows to send.")
        return True

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        data = [row_to_dict(r) for r in batch]
        payload = {"data": data}
        payload_file = "payload.json"

        # Write batch JSON to file
        try:
            with open(payload_file, "w") as f:
                json.dump(payload, f)
        except Exception as e:
            logging.error(f"Error writing payload file: {e}")
=======
def fetch_recent_data(after=None):
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return []
    try:
        cursor = conn.cursor()
        if after:
            cursor.execute("""
                SELECT id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
                       weather_temp, weather_humidity, weather_sunlight, weather_wind_speed, location, weather_fetched, device_id
                FROM moisture_data
                WHERE timestamp > ?
            """, (after,))
        else:
            cursor.execute("""
                SELECT id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
                       weather_temp, weather_humidity, weather_sunlight, weather_wind_speed, location, weather_fetched, device_id
                FROM moisture_data
            """)
        data = cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database query error: {e}")
        return []
    finally:
        conn.close()
    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "sensor_id": row[2],
            "adc_value": row[3],
            "moisture_level": row[4],
            "digital_status": row[5],
            "weather_temp": row[6],
            "weather_humidity": row[7],
            "weather_sunlight": row[8],
            "weather_wind_speed": row[9],
            "location": row[10],
            "weather_fetched": row[11],
            "device_id": row[12]
        }
        for row in data
    ]

def retry_with_backoff(func, max_attempts=RETRY_ATTEMPTS, base_delay=BASE_DELAY):
    for attempt in range(max_attempts):
        if func():
            return True
        delay = base_delay * (2 ** attempt)
        logging.warning(f"Retrying after {delay} seconds...")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False

def send_data_to_backend(after=None):
    data = fetch_recent_data(after)
    if not data:
        logging.info("No new data to send.")
        return False, None
    def send_request():
        try:
            response = requests.post(BACKEND_API_URL, json={"sensor_data": data}, timeout=10)
            if response.status_code == 200:
                logging.info("Data sent successfully.")
                return True
            else:
                logging.error(f"Failed to send data ({response.status_code}): {response.text}")
                return False
        except requests.RequestException as e:
            logging.error(f"Error sending data: {e}")
>>>>>>> origin/main
            return False
    success = retry_with_backoff(send_request)
    return success, data if success else None

<<<<<<< HEAD
        # Build a curl command that writes only the HTTP status code to stdout
        cmd = [
            "curl",
            "--location",
            "--silent",           # suppress progress meter
            "--show-error",       # but show errors
            "--write-out", "%{http_code}",  # output only status code
            "--output", "/dev/null",         # discard response body
            "--request", "POST", url,
            "--header", "Content-Type: application/json",
            "--data", f"@{payload_file}"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            http_code = result.stdout.strip()
            if result.returncode == 0 and http_code == "200":
                logging.info(f"Batch starting at row {data[0]['id']} sent successfully (HTTP 200).")
                LAST_SENT_ID = data[-1]["id"]
                save_last_sent_id(LAST_SENT_ID)
            else:
                logging.error(
                    f"Curl failed for batch at row {data[0]['id']}: exit={result.returncode}, "
                    f"http_code={http_code}, stderr={result.stderr.strip()}"
                )
                return False
        except Exception as e:
            logging.error(f"Error executing curl command: {e}")
            return False

    return True

def get_min_id_after_timestamp(ts_str):
    """
    Return the minimum row id where the database's timestamp is greater than the provided ts_str.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MIN(id) FROM moisture_data WHERE timestamp > ?",
            (ts_str,),
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] else None
    except Exception as e:
        logging.error(f"Error in get_min_id_after_timestamp: {e}")
        return None

@app.route("/send-data", methods=["POST"])
def auto_send():
    """
    Auto-send endpoint: send unsent rows in batches.
    Optionally reset LAST_SENT_ID based on an 'after' timestamp.
    """
    global LAST_SENT_ID
    req = request.get_json() or {}
    after_str = req.get("after")
    if after_str:
        new_min = get_min_id_after_timestamp(after_str)
        if new_min is not None:
            LAST_SENT_ID = new_min - 1
            save_last_sent_id(LAST_SENT_ID)
            logging.info(f"Auto-send reset LAST_SENT_ID to {LAST_SENT_ID} using after={after_str}")
    success = send_unsent_rows_via_curl(BACKEND_API_SEND_DATA)
    status = 200 if success else 500
    return jsonify({"message": "Data sent successfully" if success else "Failed to send data"}), status

@app.route("/send-current", methods=["POST"])
def manual_send():
    """
    Manual send endpoint: same as auto-send but to the CURRENT endpoint.
    """
    global LAST_SENT_ID
    req = request.get_json() or {}
    after_str = req.get("after")
    if after_str:
        new_min = get_min_id_after_timestamp(after_str)
        if new_min is not None:
            LAST_SENT_ID = new_min - 1
            save_last_sent_id(LAST_SENT_ID)
            logging.info(f"Manual-send reset LAST_SENT_ID to {LAST_SENT_ID} using after={after_str}")
    success = send_unsent_rows_via_curl(BACKEND_API_SEND_CURRENT)
    status = 200 if success else 500
    return jsonify({"message": "Current data sent successfully" if success else "Failed to send current data"}), status

def scheduled_job():
    """Scheduler job to auto-send data periodically."""
    send_unsent_rows_via_curl(BACKEND_API_SEND_DATA)

def start_scheduler():
    """Start the background scheduler."""
    schedule.every(SENSOR_READ_INTERVAL).seconds.do(scheduled_job)
    logging.info(f"Scheduler started with interval {SENSOR_READ_INTERVAL} seconds.")
=======
@app.route("/send-current", methods=["GET", "POST"])
def send_current_data():
    global LAST_SENT_TIMESTAMP
    success, data = send_data_to_backend(after=LAST_SENT_TIMESTAMP)
    if success and data:
        try:
            max_ts = max(record["timestamp"] for record in data)
            LAST_SENT_TIMESTAMP = max_ts
        except Exception as e:
            logging.error(f"Error updating LAST_SENT_TIMESTAMP: {e}")
        return jsonify({"message": "Current data sent successfully"}), 200
    elif success:
        return jsonify({"message": "No new data to send"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

@app.route("/send-data", methods=["POST"])
def send_data():
    success, _ = send_data_to_backend()
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

def safe_task_execution(task):
    try:
        task()
    except Exception as e:
        logging.error(f"Scheduled task failed: {e}")

def schedule_data_sending():
    schedule.every().day.at("00:00").do(lambda: safe_task_execution(send_data_to_backend))
    schedule.every().day.at("12:00").do(lambda: safe_task_execution(send_data_to_backend))
    logging.info("Scheduled jobs registered successfully.")
>>>>>>> origin/main
    while True:
        schedule.run_pending()
        time.sleep(1)

<<<<<<< HEAD
if __name__ == "__main__":
    # Start scheduler thread
    threading.Thread(target=start_scheduler, daemon=True).start()
    # Run Flask
=======
def run_schedule_in_thread():
    thread = threading.Thread(target=schedule_data_sending)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    run_schedule_in_thread()
>>>>>>> origin/main
    app.run(host="0.0.0.0", port=5001, debug=False)
