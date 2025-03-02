#!/usr/bin/env python3

import subprocess
import time
import sqlite3
import logging
import signal
import sys
import os
import csv
from datetime import datetime, timedelta

from config import SENSOR_READ_INTERVAL, DATA_RETENTION_DAYS, WEATHER_FETCH_INTERVAL, MIN_ADC, MAX_ADC, ENABLE_CSV_OUTPUT, CSV_FILENAME, DB_NAME
import weather_api
import sensors
import database
import utils

# Setup logging
logging.basicConfig(filename="sensor_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Start the send_data_api.py process (if not using systemd)
try:
    api_process = subprocess.Popen(["python3", "send_data_api.py"])
except Exception as e:
    logging.error(f"Failed to start send_data_api.py subprocess: {e}")
    sys.exit(1)

# Sensor configuration: each sensor uses an analog channel and a digital GPIO pin.
# (For simplicity, we define them here; you could also move these to a separate module.)
SENSORS = [
    {"analog": sensors.ADS.P0, "digital": 14, "active": True},
    {"analog": sensors.ADS.P1, "digital": 15, "active": True},
    {"analog": sensors.ADS.P2, "digital": 18, "active": True},
    {"analog": sensors.ADS.P3, "digital": 23, "active": True},
]

# Additional GPIO pins and setup.
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
ADDR_PIN = 7
ALRT_PIN = 0
GPIO.setup(ADDR_PIN, GPIO.OUT)
GPIO.setup(ALRT_PIN, GPIO.IN)
for sensor in SENSORS:
    if sensor["active"]:
        GPIO.setup(sensor["digital"], GPIO.IN)

# Global variables for database connection and retry settings.
conn = None
MAX_RETRIES = 3

# Global variables for location and weather caching.
DEVICE_LAT = None
DEVICE_LON = None
DEVICE_LOCATION = None  # Will store only the city name.
last_weather_time = 0
last_weather_data = None  # Cached weather data tuple.

# --- Function Definitions ---

def read_sensor_with_retries(sensor):
    """Attempts to read sensor data with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            return sensors.read_sensor_channel(ads, sensor)
        except Exception as e:
            logging.warning(f"Retry {attempt + 1} for sensor {sensor['analog']} due to error: {e}")
            time.sleep(1)
    logging.error(f"Failed to read sensor {sensor['analog']} after {MAX_RETRIES} attempts.")
    return 0, 0, "Error"

def handle_shutdown(signum, frame):
    """Handles graceful shutdown: cleans up GPIO, closes DB, terminates subprocess."""
    print("Received shutdown signal...")
    GPIO.cleanup()
    logging.info("GPIO Cleanup Done.")
    if conn:
        conn.close()
    api_process.terminate()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

def main_loop():
    """Main loop: sets up the database, detects location, reads sensors, and stores data."""
    global conn, DEVICE_LAT, DEVICE_LON, DEVICE_LOCATION, last_weather_time, last_weather_data
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to the database: {e}")
        sys.exit(1)
    database.setup_database(conn)
    # Detect location (lat, lon used internally; we use only the city name for display/storage)
    DEVICE_LAT, DEVICE_LON, loc_name = weather_api.detect_location()
    if loc_name:
        DEVICE_LOCATION = loc_name
    else:
        DEVICE_LOCATION = "Unknown"
    print(f"Detected device location: {DEVICE_LOCATION}")
    logging.info(f"Final device location set to: {DEVICE_LOCATION}")
    GPIO.output(ADDR_PIN, GPIO.HIGH)
    while True:
        current_sec = time.time()
        # Fetch new weather data only if interval has passed.
        if last_weather_time == 0 or (current_sec - last_weather_time) >= WEATHER_FETCH_INTERVAL:
            new_weather = weather_api.get_weather_data(DEVICE_LAT, DEVICE_LON)
            # If new_weather is valid (at least one field is not None), update cache.
            if new_weather and any(field is not None for field in new_weather):
                last_weather_data = new_weather
                last_weather_time = current_sec
        w_temp, w_humidity, w_sunlight, w_wind_speed = (last_weather_data if last_weather_data else (None, None, None, None))
        weather_fetched_str = datetime.fromtimestamp(last_weather_time).strftime('%Y-%m-%d %H:%M:%S') if last_weather_time else "Unknown"
        for index, sensor in enumerate(SENSORS, start=1):
            if not sensor["active"]:
                continue
            adc_value, moisture_level, digital_status = read_sensor_with_retries(sensor)
            print(f"Sensor {index} - ADC: {adc_value}, Moisture: {moisture_level:.2f}%, Digital: {digital_status}, "
                  f"Temp: {w_temp}, Humidity: {w_humidity}, Sunlight: {w_sunlight}, Wind: {w_wind_speed}")
            logging.info(f"Sensor {index} - ADC: {adc_value}, Moisture: {moisture_level:.2f}%, Digital: {digital_status}, "
                         f"Weather Temp: {w_temp}, Humidity: {w_humidity}, Sunlight: {w_sunlight}, Wind: {w_wind_speed}")
            # Prepare record tuple for database.
            record = (index, adc_value, moisture_level, digital_status,
                      w_temp, w_humidity, w_sunlight, w_wind_speed,
                      DEVICE_LOCATION, weather_fetched_str)
            database.save_record(conn, record)
            # Prepare CSV record.
            csv_record = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), index, adc_value, f"{moisture_level:.2f}",
                          digital_status, w_temp, w_humidity, w_sunlight, w_wind_speed,
                          DEVICE_LOCATION, weather_fetched_str]
            utils.save_to_csv(csv_record)
        database.delete_old_records(conn)
        # (Optional) You can add sensor_health_check() here if desired.
        time.sleep(SENSOR_READ_INTERVAL)

try:
    main_loop()
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
    if conn:
        conn.close()
    logging.info("GPIO Cleanup Done.")
    print("GPIO Cleanup Done.")
