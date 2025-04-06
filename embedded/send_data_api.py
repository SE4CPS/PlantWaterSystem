import os
import sqlite3
import time
import threading
import logging
import requests
import schedule
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

def fetch_next_row(last_id):
    """
    Fetch the next row (reading) from the database with id greater than last_id.
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
            LIMIT 1
            """,
            (last_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        logging.error(f"Database error in fetch_next_row: {e}")
        return None

def row_to_dict(row):
    """
    Convert a database row to a dictionary matching the required JSON structure.
    Row fields: id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
                weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
                location, weather_fetched, device_id
    """
    return {
        "id": row[0],  # Use the database row number as the id
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

def send_one_reading(url, reading):
    """
    Send a single reading (row) as JSON to the given URL.
    The JSON payload is structured to match the provided curl command.
    """
    payload = {
        "data": [
            {
                "id": reading["id"],
                "timestamp": reading["timestamp"],
                "sensor_id": reading["sensor_id"],
                "adc_value": reading["adc_value"],
                "moisture_level": reading["moisture_level"],
                "digital_status": reading["digital_status"],
                "weather_temp": reading["weather_temp"],
                "weather_humidity": reading["weather_humidity"],
                "weather_sunlight": reading["weather_sunlight"],
                "weather_wind_speed": reading["weather_wind_speed"],
                "location": reading["location"],
                "weather_fetched": reading["weather_fetched"],
                "device_id": reading["device_id"],
            }
        ]
    }
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,  # Using 15 seconds as in the old working code.
        )
        if response.status_code == 200:
            logging.info(f"Reading {reading['id']} sent successfully.")
            return True, False
        else:
            if "duplicate key" in response.text.lower() or "already exists" in response.text.lower():
                logging.error(f"Duplicate error for reading {reading['id']}: {response.text}")
                return False, True
            logging.error(f"Error sending reading {reading['id']}: {response.status_code} - {response.text}")
            return False, False
    except Exception as e:
        logging.error(f"HTTP send failed for reading {reading['id']}: {e}")
        return False, False

def retry_with_backoff(func, attempts=RETRY_ATTEMPTS, base=BASE_DELAY):
    """
    Retry a function using exponential backoff.
    Returns a tuple (success, duplicate_flag).
    """
    dup_flag = False
    for i in range(attempts):
        success, duplicate = func()
        if duplicate:
            dup_flag = True
        if success:
            return True, dup_flag
        delay = base * (2 ** i)
        logging.error(f"Retrying after {delay} seconds...")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False, dup_flag

def send_all_available(url):
    """
    Iterate through and send each row in the database (one by one) that has not been sent.
    """
    global LAST_SENT_ID
    while True:
        row = fetch_next_row(LAST_SENT_ID)
        if not row:
            break
        reading = row_to_dict(row)
        def attempt_send():
            return send_one_reading(url, reading)
        success, duplicate = retry_with_backoff(attempt_send)
        if not (success or duplicate):
            return False
        LAST_SENT_ID = reading["id"]
        save_last_sent_id(LAST_SENT_ID)
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
        if row and row[0]:
            return row[0]
        return None
    except Exception as e:
        logging.error(f"Error in get_min_id_after_timestamp: {e}")
        return None

@app.route("/send-data", methods=["POST"])
def auto_send():
    """
    Auto-send endpoint: sends every row (reading) that hasn't been sent yet,
    using the BACKEND_API_SEND_DATA URL.
    Optionally, if an 'after' timestamp is provided in the request payload,
    the LAST_SENT_ID is reset accordingly.
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
    success = send_all_available(BACKEND_API_SEND_DATA)
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

@app.route("/send-current", methods=["POST"])
def manual_send():
    """
    Manual send endpoint: sends every row (reading) that hasn't been sent yet,
    using the BACKEND_API_SEND_CURRENT URL.
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
    success = send_all_available(BACKEND_API_SEND_CURRENT)
    if success:
        return jsonify({"message": "Current data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

def scheduled_job():
    """Job for the scheduler to auto-send data at the defined interval."""
    send_all_available(BACKEND_API_SEND_DATA)

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
