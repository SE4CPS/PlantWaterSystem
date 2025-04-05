import os
import sqlite3
import time
import threading
import logging
import requests
import schedule
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

# File to persist the last successfully sent row ID (reading id)
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


# Global variable for the last sent reading id, persistent across restarts.
LAST_SENT_ID = load_last_sent_id()


def fetch_next_group(last_id):
    """
    Fetch the next complete group of sensor readings from the database.
    A group is defined as readings sharing the same timestamp with exactly
    4 rows (each with a distinct sensor_id). Returns an empty list if no group is found.
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
    except sqlite3.Error as e:
        logging.error(f"Database error in fetch_next_group: {e}")
        return []

    if not rows:
        return []

    from collections import defaultdict

    groups = defaultdict(list)
    for row in rows:
        r_id, ts, sensor_id, adc_val, moist_lvl, dig_status, w_temp, w_hum, w_sun, w_wind, loc, w_fetch, dev_id = row
        groups[ts].append({
            "id": r_id,  # Row number from the DB
            "timestamp": str(ts),  # Keep timestamp as text
            "sensor_id": sensor_id,
            "adc_value": adc_val,
            "moisture_level": round(moist_lvl, 2) if moist_lvl is not None else 0,
            "digital_status": dig_status if dig_status is not None else "",
            "weather_temp": w_temp if w_temp is not None else 0,
            "weather_humidity": w_hum if w_hum is not None else 0,
            "weather_sunlight": w_sun if w_sun is not None else 0,
            "weather_wind_speed": w_wind if w_wind is not None else 0,
            "location": loc if loc is not None else "",
            "weather_fetched": str(w_fetch) if w_fetch is not None else "",
            "device_id": dev_id if dev_id is not None else "",
        })

    # Return the first group that has exactly 4 readings with distinct sensor_ids.
    for ts_key in sorted(groups.keys()):
        group = groups[ts_key]
        if len(group) == 4 and len({g["sensor_id"] for g in group}) == 4:
            return group
    return []


def send_one_reading(url, reading):
    """
    Send a single reading as JSON to the specified URL.
    The JSON structure exactly matches your curl command example.
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
            timeout=15,
        )
        if response.status_code == 200:
            logging.info(f"Reading {reading['id']} sent successfully.")
            return True, False
        else:
            # Check if the error indicates a duplicate entry.
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


def send_next_group(url):
    """
    Fetch the next complete group of sensor readings and send each reading individually.
    If all readings in the group are sent (or if duplicates are detected), update LAST_SENT_ID.
    """
    global LAST_SENT_ID
    group = fetch_next_group(LAST_SENT_ID)
    if not group:
        logging.info("No complete group available to send.")
        return True
    max_id_in_group = max(reading["id"] for reading in group)
    for reading in group:
        def attempt_send():
            return send_one_reading(url, reading)
        success, duplicate = retry_with_backoff(attempt_send)
        if not (success or duplicate):
            return False
    LAST_SENT_ID = max_id_in_group
    save_last_sent_id(LAST_SENT_ID)
    return True


def send_all_available(url):
    """
    Loop through and send all complete groups of sensor readings until none remain.
    """
    while True:
        group = fetch_next_group(LAST_SENT_ID)
        if not group:
            break
        if not send_next_group(url):
            return False
    return True


def get_min_id_after_timestamp(ts_str):
    """
    Retrieve the minimum row id in the database for records with a timestamp
    greater than the provided ts_str.
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
    Auto-send endpoint.
    Optionally accepts an 'after' timestamp in the JSON payload to reset the LAST_SENT_ID.
    Uses the BACKEND_API_SEND_DATA URL.
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
    Manual send endpoint.
    Expects an 'after' timestamp in the JSON payload to determine which data to send.
    Uses the BACKEND_API_SEND_CURRENT URL.
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
