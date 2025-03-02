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
import database
import utils

# Hardware imports
import board
import busio
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Setup logging to file "sensor_log.log"
logging.basicConfig(filename="sensor_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize I2C interface and ADS1115 ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Start the send_data_api.py process (if not using systemd)
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
DEVICE_LOCATION = None  # Will store only the city name.
last_weather_time = 0
last_weather_data = None  # Cached tuple: (weather_temp, weather_humidity, weather_sunlight, weather_wind_speed)

# ---------------------------
# Sensor Functions (integrated directly)
# ---------------------------

def convert_adc_to_moisture(adc_value):
    """Converts a raw ADC value to a moisture percentage using MIN_ADC and MAX_ADC."""
    moisture_level = ((MAX_ADC - adc_value) / (MAX_ADC - MIN_ADC)) * 100
    return max(0, min(100, moisture_level))

def read_sensor_channel(sensor):
    """
    Reads the ADC channel and digital state for a given sensor.
    Returns a tuple: (adc_value, moisture_level, digital_status)
    """
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
    """Attempts to read sensor data with retries."""
    for
