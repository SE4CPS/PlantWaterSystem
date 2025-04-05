import os
import sqlite3
import time
import threading
import logging
import requests
import schedule
import concurrent.futures
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

# File to persist the last successfully sent timestamp
LAST_SENT_FILE = "last_sent_ts.txt"

def load_last_sent_ts():
    """Load the last sent timestamp from persistent storage. Defaults to '1970-01-01 00:00:00' if not found."""
    if os.path.exists(LAST_SENT_FILE):
        try:
            with open(LAST_SENT_FILE, "r") as f:
                content = f.read().strip()
                return content if content else "1970-01-01 00:00:00"
        except Exception as e:
            logging.error(f"Error loading LAST_SENT_TS: {e}")
    return "1970-01-01 00:00:00"

def save_last_sent_ts(ts):
    """Persist the last sent timestamp so it survives a restart."""
    try:
        with open(LAST_SENT_FILE, "w") as f:
            f.write(ts)
    except Exception as e:
        logging.error(f"Error saving LAST_SENT_TS: {e}")

# Global variable for the last sent timestamp (persistent across restarts)
LAST_SENT_TS = load_last_sent_ts()
logging.info(f"Starting with LAST_SENT_TS: {LAST_SENT_TS}")

def format_timestamp(ts):
    """
    Ensure the timestamp is a valid datetime string.
    If ts equals "LOCALTIMESTAMP" (case-insensitive), substitute with the current time.
    """
    if isinstance(ts, str) and ts.strip().upper() == "LOCALTIMESTAMP":
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ts

def fetch_unsent_groups(last_ts):
    """
    Fetch all rows from the database with timestamp greater than last_ts.
    Group rows by their timestamp and return a list of tuples (timestamp, rows),
    ordered by timestamp ascending.
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
            WHERE timestamp > ?
            ORDER BY timestamp ASC, id ASC
            """,
            (last_ts,),
        )
        rows = cursor.fetchall()
        conn.close()
        groups = {}
        for row in rows:
            ts = str(row[1])
            groups.setdefault(ts, []).append(row)
        # Return groups as a sorted list of (timestamp, rows) tuples
        sorted_groups = sorted(groups.items(), key=lambda x: x[0])
        return sorted_groups
    except Exception as e:
        logging.error(f"Error fetching unsent groups: {e}")
        return []

def row_to_dict(row):
    """
    Convert a database row to a dictionary matching the required JSON structure.
    Expected row format:
    (id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
     weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
     location, weather_fetched, device_id)
    """
    return {
        "id": row[0],  # Use the row number from the DB as id
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
    The payload structure matches your curl example.
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
            # Check for duplicate entry errors
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
    logging.error("All retry attempts failed for this reading.")
    return False, dup_flag

def send_row_with_retry(url, reading):
    """Send a single row with retry logic."""
    def attempt():
        return send_one_reading(url, reading)
    return retry_with_backoff(attempt)

def send_group(url, group):
    """
    Send all rows in a group concurrently.
    'group' is a list of rows (all with the same timestamp).
    Returns True if all rows in the group are successfully sent or marked as duplicate.
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(group)) as executor:
        future_to_reading = {
            executor.submit(send_row_with_retry, url, row_to_dict(row)): row for row in group
        }
        for future in concurrent.futures.as_completed(future_to_reading):
            try:
                success, dup = future.result()
                results.append(success or dup)
            except Exception as e:
                logging.error(f"Exception during concurrent send: {e}")
                results.append(False)
    return all(results)

def send_all_available(url):
    """
    Fetch all unsent groups (by timestamp) and send each group.
    After a group is sent successfully, update LAST_SENT_TS to that group's timestamp.
    Returns True if all groups are sent.
    """
    global LAST_SENT_TS
    groups = fetch_unsent_groups(LAST_SENT_TS)
    if not groups:
        logging.info("No new unsent rows found in the database.")
        return True
    for ts, rows in groups:
        logging.info(f"Sending group with timestamp {ts} containing {len(rows)} row(s).")
        if send_group(url, rows):
            LAST_SENT_TS = ts
            save_last_sent_ts(LAST_SENT_TS)
            logging.info(f"Group with timestamp {ts} sent successfully; updated LAST_SENT_TS.")
        else:
            logging.error(f"Failed to send group with timestamp {ts}. Stopping further attempts.")
            return False
    return True

@app.route("/send-data", methods=["POST"])
def auto_send():
    """
    Auto-send endpoint (internal service).
    Optionally accepts an "after" timestamp in the request to reset the starting point.
    Sends unsent rows using the BACKEND_API_SEND_DATA URL.
    """
    global LAST_SENT_TS
    req = request.get_json() or {}
    after_str = req.get("after")
    if after_str:
        # Reset LAST_SENT_TS to the provided value
        LAST_SENT_TS = after_str
        save_last_sent_ts(LAST_SENT_TS)
        logging.info(f"Auto-send reset LAST_SENT_TS to {LAST_SENT_TS} using provided after timestamp.")
    success = send_all_available(BACKEND_API_SEND_DATA)
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

@app.route("/send-current", methods=["POST"])
def manual_send():
    """
    Manual send endpoint (internal service).
    Requires an "after" timestamp in the request to reset the starting point.
    Sends unsent rows using the BACKEND_API_SEND_CURRENT URL.
    """
    global LAST_SENT_TS
    req = request.get_json() or {}
    after_str = req.get("after")
    if not after_str:
        logging.error("Missing 'after' field in manual send request.")
        return jsonify({"message": "Field 'after' is required"}), 400
    # Reset LAST_SENT_TS to the provided value
    LAST_SENT_TS = after_str
    save_last_sent_ts(LAST_SENT_TS)
    logging.info(f"Manual-send reset LAST_SENT_TS to {LAST_SENT_TS} using provided after timestamp.")
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
