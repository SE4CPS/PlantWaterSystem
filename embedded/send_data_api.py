#!/usr/bin/env python3

from flask import Flask, jsonify
import sqlite3
import requests
import schedule
import time
import threading
import logging
import os
from datetime import datetime, timedelta

logging.basicConfig(filename="api_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

DB_NAME = os.getenv("DB_NAME", "plant_sensor_data.db")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/sensor/data")
RETRY_ATTEMPTS = 3
BASE_DELAY = 2

app = Flask(__name__)

def fetch_recent_data():
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
                   weather_temp, weather_humidity, weather_sunlight, weather_wind_speed, location, weather_fetched
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
            "weather_fetched": row[11]
        }
        for row in data
    ]

def retry_with_backoff(func, max_attempts=3, base_delay=2):
    for attempt in range(max_attempts):
        if func():
            return True
        delay = base_delay * (2 ** attempt)
        logging.warning(f"Retrying after {delay} seconds...")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False

def send_data_to_backend():
    data = fetch_recent_data()
    if not data:
        logging.info("No data to send.")
        return False
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
    return retry_with_backoff(send_request, max_attempts=RETRY_ATTEMPTS, base_delay=BASE_DELAY)

@app.route("/send-data", methods=["POST"])
def send_data():
    if send_data_to_backend():
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
    app.run(host="0.0.0.0", port=5001)
