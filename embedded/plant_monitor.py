#!/usr/bin/env python3
"""
Plant Moisture Monitoring System

This script reads moisture sensor data via an ADS1115 ADC, fetches current weather data
(with caching every WEATHER_FETCH_INTERVAL seconds), and stores the combined data in an SQLite
database as well as a temporary CSV file. Only the location name (e.g., "Stockton, California, US")
is used for display and storage.
"""

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

# Setup logging
logging.basicConfig(filename="sensor_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Import required libraries for sensor reading
import board
import busio
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Initialize I2C interface and ADS1115 ADC instance.
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Start the send_data_api.py process (alternatively managed via systemd)
try:
    api_process = subprocess.Popen(["python3", "send_data_api.py"])
except Exception as e:
    logging.error(f"Failed to start send_data_api.py subprocess
