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
BASE_DELAY = 2  # Base delay for exponential backoff

app = Flask(__name__)

def fetch_recent_data():
    """Fetch all sensor readings from the last 12 hours."""
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to the database: {e}")
        return []

    try:
        cursor = conn.cursor()

        # Get the current timestamp and 12 hours back
        twelve_hours_ago = datetime.now() - timedelta(hours=12)

        # Query for data within the last 12 hours
        cursor.execute("""
            SELECT id, timestamp, sensor_id, moisture_level, digital_status
            FROM moisture_data
            WHERE timestamp >= ?
        """, (twelve_hours_ago.strftime("%Y-%m-%d %H:%M:%S"),))

        data = cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database query error: {e}")
        return []
    finally:
        conn.close()

    # Convert data to a list of dictionaries
    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "sensor_id": row[2],
            "moisture_level": row[3],
            "digital_status": row[4]
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
    """Send sensor data to the backend with retry logic."""
    data = fetch_recent_data()

    if not data:
        logging.info("No data to send.")
        return False

    def send_request():
        try:
            response = requests.post(BACKEND_API_URL, json={"sensor_data": data}, timeout=10)
            if response.status_code == 200:
                logging.info("Data sent successfully")
                return True
            else:
                logging.error(f"Failed to send data ({response.status_code}) - {response.text}")
                return False
        except requests.RequestException as e:
            logging.error(f"Error sending data - {e}")
            return False

    return retry_with_backoff(send_request, max_attempts=RETRY_ATTEMPTS, base_delay=BASE_DELAY)

@app.route("/send-data", methods=["POST"])
def send_data():
    """Trigger data sending via an API request."""
    if send_data_to_backend():
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

def safe_task_execution(task):
    """Execute a task safely, catching any exceptions."""
    try:
        task()
    except Exception as e:
        logging.error(f"Scheduled task failed: {e}")

def verify_schedule_registration(job):
    """Verify if the schedule is successfully registered."""
    if job is None:
        logging.error("Failed to register scheduled job.")
    else:
        logging.info("Scheduled job registered successfully.")

def schedule_data_sending():
    """Schedule data sending to occur at 12:00 AM and 12:00 PM daily."""
    job1 = schedule.every().day.at("00:00").do(lambda: safe_task_execution(send_data_to_backend))
    job2 = schedule.every().day.at("12:00").do(lambda: safe_task_execution(send_data_to_backend))

    verify_schedule_registration(job1)
    verify_schedule_registration(job2)

    while True:
        schedule.run_pending()
        time.sleep(1)

def run_schedule_in_thread():
    """Run the scheduler in a separate thread."""
    thread = threading.Thread(target=schedule_data_sending)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    run_schedule_in_thread()
    app.run(host="0.0.0.0", port=5000)
