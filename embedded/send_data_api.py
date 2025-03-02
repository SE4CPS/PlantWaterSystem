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
from config import DB_NAME, BACKEND_API_URL, RETRY_ATTEMPTS, BASE_DELAY

logging.basicConfig(filename="api_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# Global variable to store the last sent timestamp.
LAST_SENT_TIMESTAMP = None

def fetch_recent_data(after=None):
    """
    Fetches sensor records from the database.
    If 'after' is provided, only returns records with a timestamp later than 'after'.
    """
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
                       weather_temp, weather_humidity, weather_sunlight, weather_wind_speed, location, weather_fetched
                FROM moisture_data
                WHERE timestamp > ?
            """, (after,))
        else:
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

def retry_with_backoff(func, max_attempts=RETRY_ATTEMPTS, base_delay=BASE_DELAY):
    """Retries a function with exponential backoff."""
    for attempt in range(max_attempts):
        if func():
            return True
        delay = base_delay * (2 ** attempt)
        logging.warning(f"Retrying after {delay} seconds...")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False

def send_data_to_backend(after=None):
    """
    Sends sensor data to the backend API.
    If 'after' is provided, sends only records with timestamp later than 'after'.
    Returns (success, data_sent).
    """
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
    """
    On-demand endpoint: sends only new sensor records (with timestamp greater than LAST_SENT_TIMESTAMP).
    After a successful send, updates LAST_SENT_TIMESTAMP to the latest timestamp from the sent data.
    """
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
    """Endpoint to send all sensor data to the backend."""
    success, _ = send_data_to_backend()
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

def safe_task_execution(task):
    """Executes a given task and logs any exceptions."""
    try:
        task()
    except Exception as e:
        logging.error(f"Scheduled task failed: {e}")

def schedule_data_sending():
    """Schedules data sending at 00:00 and 12:00 daily."""
    schedule.every().day.at("00:00").do(lambda: safe_task_execution(send_data_to_backend))
    schedule.every().day.at("12:00").do(lambda: safe_task_execution(send_data_to_backend))
    logging.info("Scheduled jobs registered successfully.")
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_schedule_in_thread():
    """Runs the scheduler in a separate daemon thread."""
    thread = threading.Thr
