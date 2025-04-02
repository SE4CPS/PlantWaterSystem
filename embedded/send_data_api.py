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
from logging.handlers import RotatingFileHandler

# Custom filter: only allow ERROR level messages or those that contain "success" (case-insensitive)
class ErrorSuccessFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= logging.ERROR:
            return True
        if "success" in record.getMessage().lower():
            return True
        return False

# Configure the logger with a rotating file handler
handler = RotatingFileHandler("api_log.log", maxBytes=5 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
handler.addFilter(ErrorSuccessFilter())

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Remove any default handlers if necessary (optional)
for h in logger.handlers[:]:
    logger.removeHandler(h)
logger.addHandler(handler)

app = Flask(__name__)
LAST_SENT_TIMESTAMP = None  # Tracks the last sent record's timestamp

def fetch_recent_data(after=None):
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
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
            lower_bound = (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                SELECT id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
                       weather_temp, weather_humidity, weather_sunlight, weather_wind_speed, location, weather_fetched, device_id
                FROM moisture_data
                WHERE timestamp > ?
            """, (lower_bound,))
        data = cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        return []
    finally:
        conn.close()
    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "sensor_id": row[2],
            "adc_value": row[3],
            "moisture_level": round(row[4], 2),
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

def send_request_curl(url, data):
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
            logger.info("Data send success")
            return True
        else:
            logger.error(f"Curl command returned HTTP code {http_code}: {output}")
            return False
    else:
        logger.error(f"Curl command failed: {result.stderr}")
        return False

def retry_with_backoff(func, max_attempts=RETRY_ATTEMPTS, base_delay=BASE_DELAY):
    for attempt in range(max_attempts):
        if func():
            return True
        delay = base_delay * (2 ** attempt)
        logger.error(f"Retrying after {delay} seconds...")
        time.sleep(delay)
    logger.error("All retry attempts failed.")
    return False

def send_data_to_backend(url, after=None, limit_12_hours=True):
    now_dt = datetime.now()
    if limit_12_hours:
        if after is None:
            effective_after_dt = now_dt - timedelta(hours=12)
        else:
            try:
                last_dt = datetime.strptime(after, "%Y-%m-%d %H:%M:%S")
            except Exception:
                last_dt = now_dt - timedelta(hours=12)
            if now_dt - last_dt > timedelta(hours=12):
                effective_after_dt = now_dt - timedelta(hours=12)
                logger.error("Unsent data gap greater than 12 hours. Only sending last 12 hours of data.")
            else:
                effective_after_dt = last_dt
    else:
        if after is not None:
            try:
                effective_after_dt = datetime.strptime(after, "%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logger.error("Invalid 'after' timestamp provided for manual send")
                return False, None
        else:
            effective_after_dt = None

    if effective_after_dt is not None:
        effective_after = effective_after_dt.strftime("%Y-%m-%d %H:%M:%S")
        data = fetch_recent_data(after=effective_after)
    else:
        data = fetch_recent_data()

    if not data:
        logger.info("No new data to send.")
        return True, None
    def send_request():
        return send_request_curl(url, data)
    success = retry_with_backoff(send_request)
    return success, data if success else None

@app.route("/send-current", methods=["GET", "POST"])
def send_current_data():
    global LAST_SENT_TIMESTAMP
    success, data = send_data_to_backend(BACKEND_API_SEND_CURRENT, after=LAST_SENT_TIMESTAMP, limit_12_hours=True)
    if data is None:
        return jsonify({"message": "No new data to send"}), 200
    if success:
        try:
            max_ts = max(record["timestamp"] for record in data)
            LAST_SENT_TIMESTAMP = max_ts
        except Exception as e:
            logger.error(f"Error updating LAST_SENT_TIMESTAMP: {e}")
        return jsonify({"message": "Current data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

@app.route("/manual", methods=["GET", "POST"])
def send_manual_data():
    global LAST_SENT_TIMESTAMP
    req_json = request.get_json(silent=True) or {}
    after_timestamp = req_json.get("after", LAST_SENT_TIMESTAMP)
    success, data = send_data_to_backend(BACKEND_API_SEND_CURRENT, after=after_timestamp, limit_12_hours=False)
    if data is None:
        return jsonify({"message": "No new data to send"}), 200
    if success:
        try:
            max_ts = max(record["timestamp"] for record in data)
            LAST_SENT_TIMESTAMP = max_ts
        except Exception as e:
            logger.error(f"Error updating LAST_SENT_TIMESTAMP: {e}")
        return jsonify({"message": "Manual send success"}), 200
    else:
        return jsonify({"message": "Failed to send manual data"}), 500

@app.route("/send-data", methods=["POST"])
def send_data():
    success, _ = send_data_to_backend(BACKEND_API_SEND_DATA, limit_12_hours=True)
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

def safe_task_execution(task):
    try:
        task()
    except Exception as e:
        logger.error(f"Scheduled task failed: {e}")

def schedule_data_sending():
    # Schedule to send data every hour using the auto-send endpoint
    schedule.every().hour.do(lambda: safe_task_execution(lambda: send_data_to_backend(BACKEND_API_SEND_DATA, limit_12_hours=True)))
    logger.info("Scheduled jobs registered successfully.")
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
