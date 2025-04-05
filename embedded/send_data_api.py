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
from config import (
    DB_NAME,
    BACKEND_API_SEND_DATA,
    BACKEND_API_SEND_CURRENT,
    RETRY_ATTEMPTS,
    BASE_DELAY,
)

# Configure logging
logging.basicConfig(
    filename="api_log.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = Flask(__name__)

# Track the last timestamp that was successfully delivered
LAST_SENT_TIMESTAMP = None


def fetch_recent_data(after=None):
    """
    Pull rows from the local SQLite DB newer than *after* (or the past hour).
    Returns a list of dicts ready to be JSON‑serialised.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        base_query = """
            SELECT timestamp,
                   sensor_id,                 -- ✅ correct column name
                   adc_value,
                   moisture_level,
                   digital_status,
                   weather_temp,
                   weather_humidity,
                   weather_sunlight,
                   weather_wind_speed,
                   location,
                   weather_fetched,
                   device_id
            FROM moisture_data
            WHERE timestamp > ?
        """

        if after:
            cursor.execute(base_query, (after,))
        else:
            lower_bound = (
                    datetime.now() - timedelta(hours=1)
            ).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(base_query, (lower_bound,))

        rows = cursor.fetchall()

    except sqlite3.Error as e:
        logging.error(f"Database connection/query error: {e}")
        return []
    finally:
        conn.close()

    records = []
    for row in rows:
        records.append(
            {
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
                "device_id": row[11],
            }
        )
    return records


def send_request_curl(url, data):
    """
    Use curl to POST the payload.  We treat an HTTP 200 as confirmation that
    the backend accepted the data.
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
        "--header",
        "Content-Type: application/json",
        "--data-binary",
        f"@{tmp_filename}",
        "--output",
        "/dev/null",
        "--write-out",
        "%{http_code}",
        url,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    os.remove(tmp_filename)

    if result.returncode == 0:
        http_code = result.stdout.strip()
        if http_code == "200":
            logging.info("Data sent successfully.")  # ← log success as INFO
            return True, http_code
        else:
            logging.error(f"Curl returned HTTP code {http_code}")
            return False, http_code
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
    Fetch new data and push it to *url*. Returns (success, data_if_sent_or_None)
    """
    global LAST_SENT_TIMESTAMP

    try:
        provided_dt = (
            datetime.strptime(after, "%Y-%m-%d %H:%M:%S")
            if after
            else (datetime.now() - timedelta(hours=1))
        )
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
        return True, None  # nothing new is not a failure

    success = retry_with_backoff(lambda: send_request_curl(url, data)[0])
    return success, data if success else None


@app.route("/send-current", methods=["POST"])
def send_current_data():
    success, data = send_data_to_backend(BACKEND_API_SEND_CURRENT, after=LAST_SENT_TIMESTAMP)
    if data:
        LAST_SENT_TIMESTAMP = max(record["timestamp"] for record in data)
    return (
        jsonify({"message": "Current data sent successfully" if success else "Failed to send current data"}),
        200 if success else 500,
    )


@app.route("/manual", methods=["POST"])
def send_manual_data():
    req_json = request.get_json() or {}
    after_timestamp = req_json.get("after")
    if not after_timestamp:
        return jsonify({"message": "Missing 'after' timestamp in request"}), 400

    success, data = send_data_to_backend(BACKEND_API_SEND_DATA, after=after_timestamp)
    if data:
        LAST_SENT_TIMESTAMP = max(record["timestamp"] for record in data)
    return (
        jsonify({"message": "Manual data sent successfully" if success else "Failed to send manual data"}),
        200 if success else 500,
    )


@app.route("/send-data", methods=["POST"])
def send_auto_data():
    success, data = send_data_to_backend(BACKEND_API_SEND_DATA)
    if data:
        LAST_SENT_TIMESTAMP = max(record["timestamp"] for record in data)
    return (
        jsonify({"message": "Data sent successfully" if success else "Failed to send data"}),
        200 if success else 500,
    )


def scheduled_job():
    send_data_to_backend(BACKEND_API_SEND_DATA)


def schedule_data_sending():
    schedule.every(1).hours.do(scheduled_job)
    logging.info("Scheduled job registered successfully.")
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
