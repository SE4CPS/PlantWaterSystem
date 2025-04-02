import os
import json
import logging
import time
import tempfile
import subprocess
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import pool

# Import configuration (make sure DB_DSN is defined in config.py for neonDB)
from config import DB_DSN, BACKEND_API_SEND_DATA, BACKEND_API_SEND_CURRENT, RETRY_ATTEMPTS, BASE_DELAY

# Set up logging to only log errors and key success messages.
logging.basicConfig(
    filename="api_log.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)

# Global variable to store the timestamp of the last successfully sent record
LAST_SENT_TIMESTAMP = None

# Create a global connection pool for neonDB.
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=DB_DSN)
    logging.error("DB connection pool created successfully.")  # Using error-level to log key events.
except Exception as e:
    logging.error("Error creating DB connection pool: " + str(e))
    raise

def fetch_unsent_data(after_timestamp, batch_size=96):
    """
    Query the database for unsent sensor records that have a timestamp greater than after_timestamp.
    Returns at most batch_size records ordered by timestamp ascending.
    """
    query = """
        SELECT id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
               weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
               location, weather_fetched, device_id
        FROM moisture_data
        WHERE timestamp > %s
        ORDER BY timestamp ASC
        LIMIT %s;
    """
    try:
        conn = db_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(query, (after_timestamp, batch_size))
            rows = cur.fetchall()
        db_pool.putconn(conn)
        return [
            {
                "id": row[0],
                "timestamp": row[1].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[1], datetime) else row[1],
                "sensor_id": row[2],
                "adc_value": row[3],
                "moisture_level": round(row[4], 2),
                "digital_status": row[5],
                "weather_temp": row[6],
                "weather_humidity": row[7],
                "weather_sunlight": row[8],
                "weather_wind_speed": row[9],
                "location": row[10],
                "weather_fetched": row[11].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[11], datetime) else row[11],
                "device_id": row[12]
            }
            for row in rows
        ]
    except Exception as e:
        logging.error("Database query error: " + str(e))
        return []

def send_request_curl(url, data):
    """
    Write the JSON payload (with key "data") to a temporary file and use curl to POST it.
    Returns True if a 200 HTTP code is returned.
    """
    payload = json.dumps({"data": data})
    try:
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
            # Extract the last three characters as the HTTP status code.
            http_code = result.stdout.strip()[-3:]
            if http_code == "200":
                return True
            else:
                logging.error(f"Curl command returned HTTP code {http_code}: {result.stdout.strip()}")
                return False
        else:
            logging.error(f"Curl command failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error("Error in send_request_curl: " + str(e))
        return False

def retry_with_backoff(func, max_attempts=RETRY_ATTEMPTS, base_delay=BASE_DELAY):
    for attempt in range(max_attempts):
        if func():
            return True
        delay = base_delay * (2 ** attempt)
        logging.error(f"Retrying after {delay} seconds...")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False

def send_data_to_backend(url, after_timestamp, limit_batch=True):
    """
    Fetch unsent sensor data (in batches of up to 96 records) starting from after_timestamp.
    Send the batch via curl. If more than 96 records exist, only send the oldest batch.
    On success, update the global LAST_SENT_TIMESTAMP to the timestamp of the last record sent.
    """
    global LAST_SENT_TIMESTAMP

    # Convert after_timestamp to a string if needed. If None, use a very early date.
    if after_timestamp is None:
        effective_after = "1970-01-01 00:00:00"
    else:
        effective_after = after_timestamp

    data_batch = fetch_unsent_data(effective_after, batch_size=96)
    if not data_batch:
        logging.error("No new data to send.")
        return True, None

    def send_request():
        return send_request_curl(url, data_batch)

    success = retry_with_backoff(send_request)
    if success:
        # Update LAST_SENT_TIMESTAMP to the timestamp of the last record in the batch.
        try:
            last_record = data_batch[-1]
            LAST_SENT_TIMESTAMP = last_record["timestamp"]
        except Exception as e:
            logging.error("Error updating LAST_SENT_TIMESTAMP: " + str(e))
        logging.error("Data sent successfully.")
        return True, data_batch
    else:
        return False, data_batch

# Scheduler to auto-send data every 1 hour using the first API endpoint.
def schedule_auto_send():
    while True:
        # Wait until the top of the hour
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=5, microsecond=0)
        sleep_seconds = (next_hour - now).total_seconds()
        time.sleep(sleep_seconds)
        # Attempt to send data using the auto-send API.
        send_data_to_backend(BACKEND_API_SEND_DATA, LAST_SENT_TIMESTAMP, limit_batch=True)

# Start the scheduler in a background thread.
def run_scheduler_in_thread():
    import threading
    thread = threading.Thread(target=schedule_auto_send)
    thread.daemon = True
    thread.start()

@app.route("/send-data", methods=["POST"])
def auto_send_endpoint():
    """
    Endpoint to trigger auto-send manually (uses same logic as scheduled auto-send).
    """
    success, _ = send_data_to_backend(BACKEND_API_SEND_DATA, LAST_SENT_TIMESTAMP, limit_batch=True)
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

@app.route("/manual", methods=["POST"])
def manual_send():
    """
    Manual endpoint that accepts a JSON payload with an "after" timestamp.
    Sends all sensor data after that timestamp in batches (max 96 per batch).
    """
    req_json = request.get_json(silent=True) or {}
    after_ts = req_json.get("after", None)
    if not after_ts:
        return jsonify({"message": "Missing 'after' timestamp in request"}), 400

    # Here we do not limit to 6 hours worth; we simply use the provided timestamp.
    success, _ = send_data_to_backend(BACKEND_API_SEND_DATA, after_ts, limit_batch=True)
    if success:
        return jsonify({"message": "Manual send success"}), 200
    else:
        return jsonify({"message": "Manual send failed"}), 500

@app.route("/send-current", methods=["POST", "GET"])
def send_current():
    """
    On-demand endpoint to send data (using the BACKEND_API_SEND_CURRENT endpoint)
    using the same last-sent timestamp logic.
    """
    global LAST_SENT_TIMESTAMP
    success, _ = send_data_to_backend(BACKEND_API_SEND_CURRENT, LAST_SENT_TIMESTAMP, limit_batch=True)
    if success:
        return jsonify({"message": "Current data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

if __name__ == "__main__":
    run_scheduler_in_thread()
    # Run the Flask app. (Note: for production use a proper WSGI server)
    app.run(host="0.0.0.0", port=5001, debug=False)
