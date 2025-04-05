import subprocess
import time
import sqlite3
import logging
import signal
import sys
import os
import csv
from datetime import datetime, timedelta

from config import (SENSOR_READ_INTERVAL, DATA_RETENTION_DAYS, WEATHER_FETCH_INTERVAL,
                    MIN_ADC, MAX_ADC, ENABLE_CSV_OUTPUT, CSV_FILENAME, DB_NAME, DEVICE_ID)
import weather_api
import database
import utils

import board
import busio
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

logging.basicConfig(filename="sensor_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize I2C and ADS1115 instance
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Start the send_data_api.py process (managed as a subprocess)
try:
    api_process = subprocess.Popen(["python3", "send_data_api.py"])
except Exception as e:
    logging.error(f"Failed to start send_data_api.py subprocess: {e}")
    sys.exit(1)

# Sensor configurations: each sensor defined with analog channel and digital GPIO pin.
SENSORS = [
    {"analog": ADS.P0, "digital": 14, "active": True},
    {"analog": ADS.P1, "digital": 15, "active": True},
    {"analog": ADS.P2, "digital": 18, "active": True},
    {"analog": ADS.P3, "digital": 23, "active": True},
]

# Additional GPIO pins for configuration and alerts.
ADDR_PIN = 7   # For address configuration
ALRT_PIN = 0   # For alerts

GPIO.setmode(GPIO.BCM)
GPIO.setup(ADDR_PIN, GPIO.OUT)
GPIO.setup(ALRT_PIN, GPIO.IN)
for sensor in SENSORS:
    if sensor["active"]:
        GPIO.setup(sensor["digital"], GPIO.IN)

conn = None
MAX_RETRIES = 3

# Global variables for location and weather caching.
DEVICE_LAT = None
DEVICE_LON = None
DEVICE_LOCATION = None
last_weather_time = 0
last_weather_data = None

# --- Sensor Functions (integrated) ---

def convert_adc_to_moisture(adc_value):
    # Convert raw ADC value to moisture percentage
    moisture_level = ((MAX_ADC - adc_value) / (MAX_ADC - MIN_ADC)) * 100
    return round(max(0, min(100, moisture_level)), 2)

def read_sensor_channel(sensor):
    # Read the ADC value and digital state for a sensor
    try:
        chan = AnalogIn(ads, sensor["analog"])
        adc_value = chan.value
        if adc_value == 0 or adc_value > 32767:
            logging.warning(f"Sensor channel {sensor['analog']} might be disconnected.")
            return adc_value, 0, "Disconnected"
        moisture_level = convert_adc_to_moisture(adc_value)
        digital_status = "Dry" if GPIO.input(sensor["digital"]) == GPIO.HIGH else "Wet"
        return adc_value, moisture_level, digital_status
    except OSError as e:
        logging.error(f"I2C error on sensor {sensor['analog']}: {e}")
        return 0, 0, "Error"
    except Exception as e:
        logging.error(f"Unexpected error on sensor {sensor['analog']}: {e}")
        return 0, 0, "Error"

def read_sensor_with_retries(sensor):
    # Attempt to read sensor data multiple times
    for attempt in range(MAX_RETRIES):
        try:
            return read_sensor_channel(sensor)
        except Exception as e:
            logging.warning(f"Retry {attempt+1} for sensor {sensor['analog']} due to error: {e}")
            time.sleep(1)
    logging.error(f"Failed to read sensor {sensor['analog']} after {MAX_RETRIES} attempts.")
    return 0, 0, "Error"

# --- End of Sensor Functions ---

def save_to_csv(record):
    utils.save_to_csv(record)

def handle_shutdown(signum, frame):
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
    global conn, DEVICE_LAT, DEVICE_LON, DEVICE_LOCATION, last_weather_time, last_weather_data
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to DB: {e}")
        sys.exit(1)

    database.setup_database(conn)
    # Detect device location; store only the city name
    DEVICE_LAT, DEVICE_LON, loc_name = weather_api.detect_location()
    DEVICE_LOCATION = loc_name if loc_name else "Unknown"
    print(f"Detected device location: {DEVICE_LOCATION}")
    logging.info(f"Final device location: {DEVICE_LOCATION}")

    GPIO.output(ADDR_PIN, GPIO.HIGH)

    while True:
        current_sec = time.time()
        # Fetch new weather data if needed
        if last_weather_time == 0 or (current_sec - last_weather_time) >= WEATHER_FETCH_INTERVAL:
            new_weather = weather_api.get_weather_data(DEVICE_LAT, DEVICE_LON)
            if new_weather and any(field is not None for field in new_weather):
                last_weather_data = new_weather
                last_weather_time = current_sec

        w_temp, w_humidity, w_sunlight, w_wind_speed = (
            last_weather_data if last_weather_data else (None, None, None, None)
        )

        # 1) Generate a naive local time string (no offset)
        local_now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 2) Do the same for weather_fetched
        if last_weather_time:
            weather_fetched_str = datetime.fromtimestamp(last_weather_time).strftime("%Y-%m-%d %H:%M:%S")
        else:
            weather_fetched_str = "Unknown"

        # For each sensor
        for index, sensor in enumerate(SENSORS, start=1):
            if not sensor["active"]:
                continue

            adc_value, moisture_level, digital_status = read_sensor_with_retries(sensor)
            print(
                f"Sensor {index} - ADC: {adc_value}, Moisture: {moisture_level:.2f}%, "
                f"Digital: {digital_status}, Temp: {w_temp}, Humidity: {w_humidity}, "
                f"Sunlight: {w_sunlight}, Wind: {w_wind_speed}"
            )
            logging.info(
                f"Sensor {index} - ADC: {adc_value}, Moisture: {moisture_level:.2f}%, "
                f"Digital: {digital_status}, Weather Temp: {w_temp}, "
                f"Humidity: {w_humidity}, Sunlight: {w_sunlight}, Wind: {w_wind_speed}"
            )

            # Insert row into DB (the 'timestamp' field in DB is naive local time)
            record = (
                DEVICE_ID, index, adc_value, moisture_level, digital_status,
                w_temp, w_humidity, w_sunlight, w_wind_speed,
                DEVICE_LOCATION, weather_fetched_str
            )
            database.save_record(conn, record)

            # Write row to CSV
            csv_record = [
                local_now_str,
                DEVICE_ID,
                index,
                adc_value,
                f"{moisture_level:.2f}",
                digital_status,
                w_temp,
                w_humidity,
                w_sunlight,
                w_wind_speed,
                DEVICE_LOCATION,
                weather_fetched_str
            ]
            save_to_csv(csv_record)

        database.delete_old_records(conn)
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