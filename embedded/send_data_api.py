import os
import json
import time
import logging
import sqlite3
import schedule
import subprocess
import tempfile
import threading
from datetime import datetime
from flask import Flask, request, jsonify

# Import all relevant settings from config.py
from config import (
    DB_NAME,
    BACKEND_API_SEND_DATA,
    BACKEND_API_SEND_CURRENT,
    RETRY_ATTEMPTS,
    BASE_DELAY,
    # If you'd like, define CHUNK_SIZE=96 in config.py and import it:
    # CHUNK_SIZE,
)

# If CHUNK_SIZE is not defined in config, define it here:
CHUNK_SIZE = 96

logging.basicConfig(
    filename="api_log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Single global last-sent timestamp used by all endpoints
LAST_SENT_TIMESTAMP = None

app = Flask(__name__)


def fetch_data_after(timestamp):
    """
    Query the DB for all records whose timestamp is strictly greater than 'timestamp'.
    The timestamp is a string, e.g. "YYYY-MM-DD HH:MM:SS".
    Returns a list of dict, each containing:
      {
        "id": int,
        "timestamp": str,
        "sensor_id": int,
        "adc_value": float,
        "moisture_level": float,
        "digital_status": str,
        "weather_temp": float,
        "weather_humidity": float,
        "weather_sunlight": float,
        "weather_wind_speed": float,
        "location": str,
        "weather_fetched": str,
        "device_id": str
      }
    """
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return []

    data = []
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT
              id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
              weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
              location, weather_fetched, device_id
            FROM moisture_data
            WHERE timestamp > ?
            ORDER BY timestamp ASC
            """,
            (timestamp,)
        )
        rows = c.fetchall()
        for row in rows:
            record = {
                "id": row[0],
                "timestamp": row[1],
                "sensor_id": row[2],
                "adc_value": float(row[3]),
                "moisture_level": float(f"{row[4]:.2f}"),
                "digital_status": row[5],
                "weather_temp": row[6],
                "weather_humidity": row[7],
                "weather_sunlight": row[8],
                "weather_wind_speed": row[9],
                "location": row[10],
                "weather_fetched": row[11],
                "device_id": row[12]
            }
            data.append(record)
    except sqlite3.Error as e:
        logging.error(f"Database query error: {e}")
    finally:
        conn.close()

    return data


def chunkify(records, chunk_size=CHUNK_SIZE):
    """
    Break records into sub-lists of size up to chunk_size.
    """
    for i in range(0, len(records), chunk_size):
        yield records[i:i + chunk_size]


def send_request_curl(url, chunk):
    """
    Sends a single chunk of data to the given URL using curl.
    The payload must have 'data' as the root key per the backend format.
    """
    payload = json.dumps({"data": chunk})
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
        tmp_file.write(payload)
        tmp_filename = tmp_file.name

    cmd = [
        "curl", "--location", "--silent", "--show-error",
        "--header", "Content-Type: application/json",
        "--data-binary", f"@{tmp_filename}",
        "--write-out", "%{http_code}",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(tmp_filename)

    if result.returncode != 0:
        logging.error(f"Curl command failed: {result.stderr}")
        return False

    output = result.stdout.strip()
    http_code = output[-3:]
    if http_code == "200":
        return True
    else:
        logging.error(f"Curl returned HTTP code {http_code}. Output: {output}")
        return False


def retry_with_backoff(func):
    """
    Retries a function with exponential backoff, up to RETRY_ATTEMPTS.
    Returns True if success, False if repeated failures.
    """
    for attempt in range(RETRY_ATTEMPTS):
        if func():
            return True
        delay = BASE_DELAY * (2 ** attempt)
        logging.warning(f"Chunk send failed. Retrying after {delay} seconds...")
        time.sleep(delay)
    logging.error("All retry attempts for this chunk have failed.")
    return False


def send_in_chunks(url, records, last_ts):
    """
    Takes a list of 'records' and sends them in chunk_size increments to 'url'.
    If any chunk fails after RETRY_ATTEMPTS, we stop.
    On success, we update the last-sent timestamp to the last record's timestamp in that chunk.

    returns (success, updated_ts):
      success: bool
      updated_ts: final timestamp if success, else the original last_ts
    """
    current_ts = last_ts
    for chunk in chunkify(records, CHUNK_SIZE):
        def attempt_chunk():
            return send_request_curl(url, chunk)
        success = retry_with_backoff(attempt_chunk)
        if not success:
            return False, current_ts
        # If we succeeded, update current_ts to the last record in the chunk
        current_ts = chunk[-1]["timestamp"]
    return True, current_ts


def get_last_sent():
    """
    Retrieve the global LAST_SENT_TIMESTAMP, defaulting to a far-past date if None.
    """
    global LAST_SENT_TIMESTAMP
    if LAST_SENT_TIMESTAMP is None:
        LAST_SENT_TIMESTAMP = "1970-01-01 00:00:00"
    return LAST_SENT_TIMESTAMP


def set_last_sent(ts):
    """
    Update the global LAST_SENT_TIMESTAMP.
    """
    global LAST_SENT_TIMESTAMP
    LAST_SENT_TIMESTAMP = ts


@app.route("/auto", methods=["POST"])
def auto_send():
    """
    Auto-sends data (hourly) using the first API (BACKEND_API_SEND_DATA).
    Sends all data after get_last_sent(), in up to 96-record chunks.
    """
    last_ts = get_last_sent()
    records = fetch_data_after(last_ts)
    if not records:
        logging.info("Auto-sender: No new data.")
        return jsonify({"message": "No new data"}), 200

    success, updated_ts = send_in_chunks(BACKEND_API_SEND_DATA, records, last_ts)
    if success:
        set_last_sent(updated_ts)
        return jsonify({"message": "Auto send success"}), 200
    else:
        return jsonify({"message": "Auto send failed"}), 500


@app.route("/on-demand", methods=["POST"])
def on_demand():
    """
    Called by the backend to get data from the second API (BACKEND_API_SEND_CURRENT).
    We still use the same global 'last sent' timestamp to avoid re-sending duplicates.
    """
    last_ts = get_last_sent()
    records = fetch_data_after(last_ts)
    if not records:
        logging.info("On-demand: No new data.")
        return jsonify({"message": "No new data"}), 200

    success, updated_ts = send_in_chunks(BACKEND_API_SEND_CURRENT, records, last_ts)
    if success:
        set_last_sent(updated_ts)
        return jsonify({"message": "On-demand send success"}), 200
    else:
        return jsonify({"message": "On-demand send failed"}), 500


@app.route("/manual", methods=["POST"])
def manual_send():
    """
    Manual endpoint for chunked send using the first API (BACKEND_API_SEND_DATA).
    If user provides {"after": "..."} in JSON, we start from that; otherwise we start from last-sent timestamp.
    """
    req_data = request.get_json(silent=True) or {}
    after_ts = req_data.get("after", get_last_sent())

    records = fetch_data_after(after_ts)
    if not records:
        return jsonify({"message": "No new data"}), 200

    success, updated_ts = send_in_chunks(BACKEND_API_SEND_DATA, records, after_ts)
    if success:
        set_last_sent(updated_ts)
        return jsonify({"message": "Manual send success"}), 200
    else:
        return jsonify({"message": "Manual send failed"}), 500


def schedule_auto():
    """
    Schedules the auto endpoint to run once every hour.
    """
    schedule.every().hour.do(lambda: auto_send())


def schedule_runner():
    """
    Background thread to run the schedule every second.
    """
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    logging.info("Starting up send_data_api with hourly scheduling...")

    # Register the auto-send job
    schedule_auto()

    # Launch the scheduling thread
    t = threading.Thread(target=schedule_runner, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=5001, debug=False)
