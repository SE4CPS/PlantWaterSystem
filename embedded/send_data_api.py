from flask import Flask, jsonify, request
import sqlite3
import requests
import schedule
import time
import threading
import logging
import os
from datetime import datetime, timedelta
from config import DB_NAME, BACKEND_API_URL, RETRY_ATTEMPTS, BASE_DELAY

logging.basicConfig(filename="api_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
LAST_SENT_TIMESTAMP = None  # Tracks last sent timestamp

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
            return False
    success = retry_with_backoff(send_request)
    return success, data if success else None

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
