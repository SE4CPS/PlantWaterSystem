#!/usr/bin/env python3
from flask import Flask, jsonify, request
import sqlite3
import requests
import schedule
import time
import threading
import logging
import os
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(filename="api_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
DB_NAME = os.getenv("DB_NAME", "plant_sensor_data.db")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "https://backend.example.com/receive-data")
RETRY_ATTEMPTS = 3
BASE_DELAY = 2  # Base delay for exponential backoff in seconds

app = Flask(__name__)

def fetch_recent_data():
    """Fetch sensor readings from the last 12 hours."""
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return []

    try:
        cursor = conn.cursor()
        twelve_hours_ago = datetime.now() - timedelta(hours=12)
        cursor.execute("""
            SELECT id, timestamp, sensor_id, moisture_level, digital_status,
                   weather_temp, weather_humidity, weather_sunlight, weather_wind_speed
            FROM moisture_data
            WHERE timestamp >= ?
        """, (twelve_hours_ago.strftime("%Y-%m-%d %H:%M:%S"),))
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
            "moisture_level": row[3],
            "digital_status": row[4],
            "weather_temp": row[5],
            "weather_humidity": row[6],
            "weather_sunlight": row[7],
            "weather_wind_speed": row[8]
        }
        for row in data
    ]

def retry_with_backoff(func, max_attempts=3, base_delay=2):
    """Retry a function with exponential backoff."""
    for attempt in range(max_attempts):
        if func():
            return True
        delay = base_delay * (2 ** attempt)
        logging.warning(f"Retrying after {delay} seconds...")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False

def send_data_to_backend():
    """Send sensor data to the backend using retry logic."""
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
    """API endpoint to trigger data sending."""
    if send_data_to_backend():
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

def safe_task_execution(task):
    """Execute a scheduled task safely."""
    try:
        task()
    except Exception as e:

