import os
import sqlite3
import time
import threading
import logging
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

app = Flask(__name__)

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

def format_timestamp(ts):
    """
    Ensure the timestamp is a valid datetime string.
    If ts equals "LOCALTIMESTAMP" (case-insensitive), replace it with the current time.
    """
    if isinstance(ts, str) and ts.strip().upper() == "LOCALTIMESTAMP":
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ts

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
    Row fields: id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
                weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
                location, weather_fetched, device_id
    """
    return {
        "id": row[0],
        "timestamp": format_timestamp(str(row[1])),
        "sensor_id": row[2],
        "adc_value": row[3],
        "moisture_level": round(row[4], 2) if row[4] is not None else 0,
        "digital_status": row[5] if row[5] is not None else "",
        "weather_temp": row[6] if row[6] is not None else 0,
        "weather_humidity": row[7] if row[7] is not None else 0,
        "weather_sunlight": row[8] if row[8] is not None else 0,
        "weather_wind_speed": row[9] if row[9] is not None else 0,
        "location": row[10] if row[10] is not None else "",
        "weather_fetched": format_timestamp(str(row[11])) if row[11] is not None else "",
        "device_id": row[12] if row[12] is not None else "",
    }

def send_unsent_rows_via_curl(url):
    """
    Fetch all unsent rows (with id > LAST_SENT_ID), convert them into a JSON payload,
    and send the payload using a curl command.
    On success, update LAST_SENT_ID to the ID of the last row sent.
    """
    global LAST_SENT_ID
    rows = fetch_all_unsent_rows(LAST_SENT_ID)
    if not rows:
        logging.info("No unsent rows to send.")
        return True

    data = [row_to_dict(r) for r in rows]
    payload = {"data": data}
    payload_filename = "payload.json"
    try:
        with open(payload_filename, "w") as f:
            json.dump(payload, f)
    except Exception as e:
        logging.error(f"Error writing payload file: {e}")
        return False

    cmd = [
        "curl",
        "--location",
        "--request", "POST",
        url,
        "--header", "Content-Type: application/json",
        "--data", f"@{payload_filename}"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info(f"Payload sent successfully via curl: {result.stdout}")
            # Update LAST_SENT_ID to the id of the last row in our payload
            LAST_SENT_ID = data[-1]["id"]
            save_last_sent_id(LAST_SENT_ID)
            return True
        else:
            logging.error(f"Curl command failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error executing curl command: {e}")
        return False

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
        if row and row[0]:
            return row[0]
        return None
    except Exception as e:
        logging.error(f"Error in get_min_id_after_timestamp: {e}")
        return None

@app.route("/send-data", methods=["POST"])
def auto_send():
    """
    Auto-send endpoint: converts all unsent rows from the database into a JSON payload and
    sends it using curl to the BACKEND_API_SEND_DATA URL.
    Optionally, if an 'after' timestamp is provided in the JSON payload, the LAST_SENT_ID is reset.
    """
    global LAST_SENT_ID
    req = request.get_json() or {}
    after_str = req.get("after")
    if after_str:
        new_min = get_min_id_after_timestamp(after_str)
        if new_min is not None:
            LAST_SENT_ID = new_min - 1
            save_last_sent_id(LAST_SENT_ID)
            logging.info(f"Auto-send reset LAST_SENT_ID to {LAST_SENT_ID} using after timestamp {after_str}.")
    success = send_unsent_rows_via_curl(BACKEND_API_SEND_DATA)
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

@app.route("/send-current", methods=["POST"])
def manual_send():
    """
    Manual send endpoint: converts all unsent rows from the database into a JSON payload and
    sends it using curl to the BACKEND_API_SEND_CURRENT URL.
    Expects an 'after' timestamp in the JSON payload.
    """
    global LAST_SENT_ID
    req = request.get_json() or {}
    after_str = req.get("after")
    if after_str:
        new_min = get_min_id_after_timestamp(after_str)
        if new_min is not None:
            LAST_SENT_ID = new_min - 1
            save_last_sent_id(LAST_SENT_ID)
            logging.info(f"Manual-send reset LAST_SENT_ID to {LAST_SENT_ID} using after timestamp {after_str}.")
    success = send_unsent_rows_via_curl(BACKEND_API_SEND_CURRENT)
    if success:
        return jsonify({"message": "Current data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

def scheduled_job():
    """Job for the scheduler to auto-send data at the defined interval."""
    send_unsent_rows_via_curl(BACKEND_API_SEND_DATA)

def start_scheduler():
    """Start the scheduler to run the auto-send job every SENSOR_READ_INTERVAL seconds."""
    schedule.every(SENSOR_READ_INTERVAL).seconds.do(scheduled_job)
    logging.info(f"Scheduler started with interval {SENSOR_READ_INTERVAL} seconds.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Start the scheduler in a background thread.
    threading.Thread(target=start_scheduler, daemon=True).start()
    # Run the Flask app.
    app.run(host="0.0.0.0", port=5001, debug=False)
