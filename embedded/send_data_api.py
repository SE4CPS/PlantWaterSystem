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

# ───────────────────────────
# Persisting Last-Sent Timestamp
# ───────────────────────────

LAST_SENT_FILE = "last_sent_ts.txt"

def load_last_sent_ts():
    """
    Load the last sent timestamp from persistent storage.
    Defaults to '1970-01-01 00:00:00' if not found or empty.
    """
    if os.path.exists(LAST_SENT_FILE):
        try:
            with open(LAST_SENT_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    return content
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

LAST_SENT_TS = load_last_sent_ts()
logging.info(f"Starting with LAST_SENT_TS: {LAST_SENT_TS}")

# ───────────────────────────
# Database Fetch and Grouping
# ───────────────────────────

def fetch_unsent_groups(last_ts):
    """
    Fetch all rows from 'moisture_data' with timestamp > last_ts.
    Group them by their timestamp (the exact string from the DB).
    Return a list of (timestamp_str, [rows]) sorted by timestamp ascending.
    Each 'row' is a tuple of columns from moisture_data.
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
            # row[1] is the DB's 'timestamp' column
            ts_str = str(row[1])
            groups.setdefault(ts_str, []).append(row)

        # Convert dict to a sorted list of (timestamp_str, row_list)
        sorted_groups = sorted(groups.items(), key=lambda x: x[0])
        return sorted_groups

    except Exception as e:
        logging.error(f"Error fetching unsent groups: {e}")
        return []

# ───────────────────────────
# Converting Rows to JSON
# ───────────────────────────

def row_to_dict(row):
    """
    Convert one DB row into the JSON structure the backend expects.
    row format:
      (id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
       weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
       location, weather_fetched, device_id)
    """
    return {
        "id": row[0],                            # DB row ID
        "timestamp": str(row[1]),                # EXACT timestamp from DB
        "sensor_id": row[2],
        "adc_value": row[3],
        "moisture_level": round(row[4], 2) if row[4] is not None else 0,
        "digital_status": row[5] or "",
        "weather_temp": row[6] or 0,
        "weather_humidity": row[7] or 0,
        "weather_sunlight": row[8] or 0,
        "weather_wind_speed": row[9] or 0,
        "location": row[10] or "",
        "weather_fetched": str(row[11]) if row[11] else "",
        "device_id": row[12] or "",
    }

# ───────────────────────────
# Sending to External Backend
# ───────────────────────────

def send_one_reading(url, reading):
    """
    Send a single reading to the external backend. The payload matches your curl example.
    We do NOT overwrite 'timestamp'; we send the exact DB value.
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
        resp = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            logging.info(f"Reading {reading['id']} (ts={reading['timestamp']}) sent successfully.")
            return True, False
        else:
            # Check for "duplicate key" or "already exists" errors
            txt = resp.text.lower()
            if "duplicate key" in txt or "already exists" in txt:
                logging.error(f"Duplicate error for reading {reading['id']}: {resp.text}")
                return False, True
            logging.error(f"Error sending reading {reading['id']}: {resp.status_code} - {resp.text}")
            return False, False
    except Exception as e:
        logging.error(f"HTTP send failed for reading {reading['id']}: {e}")
        return False, False

def retry_with_backoff(func, attempts=RETRY_ATTEMPTS, base=BASE_DELAY):
    """
    Retry a function using exponential backoff.
    Returns (success, duplicate_flag).
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

def send_row_with_retry(url, row):
    """
    Convert the DB row to a dictionary, then attempt sending with retries.
    """
    reading_dict = row_to_dict(row)
    def attempt():
        return send_one_reading(url, reading_dict)
    return retry_with_backoff(attempt)

# ───────────────────────────
# Concurrency + Group Sending
# ───────────────────────────

def send_group(url, rows):
    """
    Send all rows in 'rows' concurrently. They all share the same timestamp.
    Returns True if every row is sent or marked duplicate, False otherwise.
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(rows)) as executor:
        future_map = {executor.submit(send_row_with_retry, url, r): r for r in rows}
        for future in concurrent.futures.as_completed(future_map):
            try:
                success, duplicate = future.result()
                results.append(success or duplicate)
            except Exception as e:
                logging.error(f"Exception in concurrent send: {e}")
                results.append(False)
    return all(results)

def send_all_available(url):
    """
    Fetch unsent groups (timestamp > LAST_SENT_TS) in ascending order.
    For each group, send concurrently. If successful, update LAST_SENT_TS to that group's timestamp.
    If any group fails, stop and return False.
    """
    global LAST_SENT_TS

    groups = fetch_unsent_groups(LAST_SENT_TS)
    if not groups:
        logging.info("No new unsent rows found in the database.")
        return True

    for ts_str, rows in groups:
        logging.info(f"Sending group with timestamp {ts_str} containing {len(rows)} row(s).")
        ok = send_group(url, rows)
        if ok:
            # Once the entire group is sent, update the last-sent timestamp
            LAST_SENT_TS = ts_str
            save_last_sent_ts(LAST_SENT_TS)
            logging.info(f"Group with timestamp {ts_str} sent successfully; updated LAST_SENT_TS.")
        else:
            logging.error(f"Failed to send group with timestamp {ts_str}. Stopping further attempts.")
            return False

    return True

# ───────────────────────────
# Flask Endpoints
# ───────────────────────────

@app.route("/send-data", methods=["POST"])
def auto_send():
    """
    Auto-send endpoint. Optionally accepts an "after" timestamp in the JSON payload
    to reset the LAST_SENT_TS. Then sends all unsent data using BACKEND_API_SEND_DATA.
    """
    global LAST_SENT_TS
    req = request.get_json() or {}
    after_str = req.get("after")
    if after_str:
        LAST_SENT_TS = after_str
        save_last_sent_ts(LAST_SENT_TS)
        logging.info(f"Auto-send: Reset LAST_SENT_TS to {LAST_SENT_TS} via 'after'.")
    success = send_all_available(BACKEND_API_SEND_DATA)
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

@app.route("/send-current", methods=["POST"])
def manual_send():
    """
    Manual-send endpoint. Requires an "after" timestamp in the JSON payload
    to reset the LAST_SENT_TS. Then sends all unsent data using BACKEND_API_SEND_CURRENT.
    """
    global LAST_SENT_TS
    req = request.get_json() or {}
    after_str = req.get("after")
    if not after_str:
        logging.error("Missing 'after' field in manual send request.")
        return jsonify({"message": "Field 'after' is required"}), 400

    LAST_SENT_TS = after_str
    save_last_sent_ts(LAST_SENT_TS)
    logging.info(f"Manual-send: Reset LAST_SENT_TS to {LAST_SENT_TS} via 'after'.")
    success = send_all_available(BACKEND_API_SEND_CURRENT)
    if success:
        return jsonify({"message": "Current data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

# ───────────────────────────
# Scheduler
# ───────────────────────────

def scheduled_job():
    """Automatically send any new data to BACKEND_API_SEND_DATA at intervals."""
    send_all_available(BACKEND_API_SEND_DATA)

def start_scheduler():
    schedule.every(SENSOR_READ_INTERVAL).seconds.do(scheduled_job)
    logging.info(f"Scheduler started with interval {SENSOR_READ_INTERVAL} seconds.")
    while True:
        schedule.run_pending()
        time.sleep(1)

# ───────────────────────────
# Main Entry Point
# ───────────────────────────

if __name__ == "__main__":
    # Start the scheduler in a background thread
    threading.Thread(target=start_scheduler, daemon=True).start()
    # Run the Flask app
    app.run(host="0.0.0.0", port=5001, debug=False)
