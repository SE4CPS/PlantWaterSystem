#!/usr/bin/env python3

import subprocess
import time
import sqlite3
import board
import busio
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import logging
import signal
import sys
import os
import csv
from datetime import datetime, timedelta

import weather_api  # Module for geolocation and weather data retrieval

# ===========================
# User Configuration Section
# ===========================
SENSOR_READ_INTERVAL = 900         # Seconds between sensor readings
DATA_RETENTION_DAYS = 7           # Days to retain data in the database
WEATHER_FETCH_INTERVAL = 900       # Seconds between weather API calls
MIN_ADC = 5000                    # ADC value corresponding to 100% moisture
MAX_ADC = 20000                   # ADC value corresponding to 0% moisture
ENABLE_CSV_OUTPUT = True          # Set to True to also output data to CSV
CSV_FILENAME = "plant_data_temp.csv"  # Temporary CSV file name
# ===========================
# End of User Configuration
# ===========================

# Global configuration variable for database name
DB_NAME = os.getenv("DB_NAME", "plant_sensor_data.db")

# Setup logging to file "sensor_log.log"
logging.basicConfig(filename="sensor_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize I2C interface and ADS1115 ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Start the send_data_api.py process (alternatively managed via systemd)
try:
    api_process = subprocess.Popen(["python3", "send_data_api.py"])
except Exception as e:
    logging.error(f"Failed to start send_data_api.py subprocess: {e}")
    sys.exit(1)

# Sensor configuration: each sensor uses an analog channel and a digital GPIO pin.
SENSORS = [
    {"analog": ADS.P0, "digital": 14, "active": True},
    {"analog": ADS.P1, "digital": 15, "active": True},
    {"analog": ADS.P2, "digital": 18, "active": True},
    {"analog": ADS.P3, "digital": 23, "active": True},
]

# Additional GPIO pins for configuration and alerts.
ADDR_PIN = 7   # GPIO pin for address configuration.
ALRT_PIN = 0   # GPIO pin for alerts.

# Setup GPIO mode and pins.
GPIO.setmode(GPIO.BCM)
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
DEVICE_LOCATION = None  # This will store only the city name, e.g., "Stockton, California, US"
last_weather_time = 0
last_weather_data = None  # Cached tuple: (temp, humidity, sunlight, wind_speed)

# ---------------------------
# Function Definitions
# ---------------------------

# Writes a record to a CSV file (if enabled).
def save_to_csv(record):
    if not ENABLE_CSV_OUTPUT:
        return
    file_exists = os.path.isfile(CSV_FILENAME)
    try:
        with open(CSV_FILENAME, mode="a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                header = ["timestamp", "sensor_id", "adc_value", "moisture_level", "digital_status",
                          "weather_temp", "weather_humidity", "weather_sunlight",
                          "weather_wind_speed", "location", "weather_fetched"]
                writer.writerow(header)
            writer.writerow(record)
    except Exception as e:
        logging.error(f"Error writing to CSV file: {e}")

# Reads sensor data with retries in case of transient errors.
def read_sensor_with_retries(sensor):
    for attempt in range(MAX_RETRIES):
        try:
            return read_sensor_channel(sensor)
        except Exception as e:
            logging.warning(f"Retry {attempt + 1} for sensor {sensor['analog']} due to error: {e}")
            time.sleep(1)
    logging.error(f"Failed to read sensor {sensor['analog']} after {MAX_RETRIES} attempts.")
    return 0, 0, "Error"

# Handles graceful shutdown by cleaning up GPIO, closing the DB, and terminating subprocess.
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

# Creates or updates the SQLite database table with columns for sensor data, weather data,
# location (only city name), raw ADC value, and weather fetch timestamp.
def setup_database():
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moisture_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sensor_id INTEGER,
            adc_value REAL,
            moisture_level REAL,
            digital_status TEXT,
            weather_temp REAL,
            weather_humidity REAL,
            weather_sunlight REAL,
            weather_wind_speed REAL,
            location TEXT,
            weather_fetched TEXT
        )
    """)
    conn.commit()
    try:
        cursor.execute("ALTER TABLE moisture_data ADD COLUMN adc_value REAL")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE moisture_data ADD COLUMN location TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE moisture_data ADD COLUMN weather_fetched TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

# Inserts a record into the database.
def save_to_database(sensor_id, adc_value, moisture_level, digital_status,
                     weather_temp, weather_humidity, weather_sunlight,
                     weather_wind_speed, location, weather_fetched):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO moisture_data 
            (sensor_id, adc_value, moisture_level, digital_status,
             weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
             location, weather_fetched)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (sensor_id, adc_value, moisture_level, digital_status,
              weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
              location, weather_fetched))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")

# Converts a raw ADC value to a moisture percentage using MIN_ADC and MAX_ADC.
def convert_adc_to_moisture(adc_value):
    moisture_level = ((MAX_ADC - adc_value) / (MAX_ADC - MIN_ADC)) * 100
    return max(0, min(100, moisture_level))

# Reads the ADC value and digital state from a sensor.
def read_sensor_channel(sensor):
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

# Reads all sensors, obtains weather data (using cache), and saves records to the DB and CSV.
def read_sensors():
    global last_weather_time, last_weather_data
    current_sec = time.time()
    if last_weather_time == 0 or (current_sec - last_weather_time) >= WEATHER_FETCH_INTERVAL:
        last_weather_data = weather_api.get_weather_data(DEVICE_LAT, DEVICE_LON)
        last_weather_time = current_sec
    w_temp, w_humidity, w_sunlight, w_wind_speed = (
        last_weather_data if last_weather_data is not None else (None, None, None, None)
    )
    weather_fetched_str = datetime.fromtimestamp(last_weather_time).strftime('%Y-%m-%d %H:%M:%S') if last_weather_time else "Unknown"
    for index, sensor in enumerate(SENSORS, start=1):
        if not sensor["active"]:
            continue
        adc_value, moisture_level, digital_status = read_sensor_with_retries(sensor)
        print(f"Sensor {index} - ADC: {adc_value}, Moisture: {moisture_level:.2f}%, Digital: {digital_status}, Temp: {w_temp}, Humidity: {w_humidity}, Sunlight: {w_sunlight}, Wind: {w_wind_speed}")
        logging.info(f"Sensor {index} - ADC: {adc_value}, Moisture: {moisture_level:.2f}%, Digital: {digital_status}, Weather Temp: {w_temp}, Humidity: {w_humidity}, Sunlight: {w_sunlight}, Wind: {w_wind_speed}")
        # Save record to database.
        save_to_database(index, adc_value, moisture_level, digital_status,
                         w_temp, w_humidity, w_sunlight, w_wind_speed,
                         DEVICE_LOCATION, weather_fetched_str)
        # Also save to CSV as temporary backup.
        record = [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), index, adc_value, f"{moisture_level:.2f}", digital_status,
                  w_temp, w_humidity, w_sunlight, w_wind_speed, DEVICE_LOCATION, weather_fetched_str]
        save_to_csv(record)
    if GPIO.input(ALRT_PIN) == GPIO.HIGH:
        print("Alert! Check sensor readings.")
        logging.warning("Alert triggered on ALRT_PIN.")

# Deletes records older than DATA_RETENTION_DAYS from the database.
def manage_data_retention():
    try:
        cutoff_date = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM moisture_data WHERE timestamp < ?",
                       (cutoff_date.strftime("%Y-%m-%d %H:%M:%S"),))
        conn.commit()
        logging.info(f"Old data deleted up to {cutoff_date}.")
    except sqlite3.Error as e:
        logging.error(f"Data retention error: {e}")

# Performs a health check on sensor data and logs warnings if average moisture is too low.
def sensor_health_check():
    try:
        cursor = conn.cursor()
        for sensor_id in range(1, len(SENSORS) + 1):
            if not SENSORS[sensor_id - 1]["active"]:
                continue
            cursor.execute("SELECT AVG(moisture_level) FROM moisture_data WHERE sensor_id = ?", (sensor_id,))
            avg_moisture = cursor.fetchone()[0]
            if avg_moisture is None:
                logging.warning(f"No data recorded for Sensor {sensor_id}.")
            elif avg_moisture < 10:
                logging.warning(f"Low average moisture for Sensor {sensor_id}: {avg_moisture:.2f}%")
    except sqlite3.Error as e:
        logging.error(f"Health check error: {e}")

# Main function: connects to the database, detects location, and enters the monitoring loop.
def main():
    global conn, DEVICE_LAT, DEVICE_LON, DEVICE_LOCATION
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to the database: {e}")
        sys.exit(1)
    setup_database()
    # Detect location; we still fetch lat and lon for weather data, but we only use the city name for display.
    DEVICE_LAT, DEVICE_LON, loc_name = weather_api.detect_location()
    if loc_name:
        DEVICE_LOCATION = loc_name  # Only store/display the city name.
    else:
        DEVICE_LOCATION = "Unknown"
    print(f"Detected device location: {DEVICE_LOCATION}")
    logging.info(f"Final device location set to: {DEVICE_LOCATION}")
    print("Starting Multi-Sensor Plant Monitoring...")
    GPIO.output(ADDR_PIN, GPIO.HIGH)
    while True:
        read_sensors()
        manage_data_retention()
        sensor_health_check()
        time.sleep(SENSOR_READ_INTERVAL)

try:
    main()
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
    if conn:
        conn.close()
    logging.info("GPIO Cleanup Done.")
    print("GPIO Cleanup Done.")
