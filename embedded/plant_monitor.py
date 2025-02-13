import subprocess  # Import subprocess to manage the API script
import time
import sqlite3
import board
import busio
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import logging
import argparse
import signal
import sys
import os
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(filename="sensor_log.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Argument parser for configurable parameters
parser = argparse.ArgumentParser()
parser.add_argument("--interval", type=int, default=10, help="Sensor read interval in seconds")
parser.add_argument("--retention_days", type=int, default=7, help="Data retention period in days")
args = parser.parse_args()

# Database and Interval Setup
DB_NAME = os.getenv("DB_NAME", "plant_sensor_data.db")
READ_INTERVAL = args.interval
RETENTION_DAYS = args.retention_days

# I2C Setup
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Start `send_data_api.py` subprocess with error handling
try:
    api_process = subprocess.Popen(["python3", "send_data_api.py"])
except Exception as e:
    logging.error(f"Failed to start send_data_api.py subprocess: {e}")
    sys.exit(1)

# Sensor Configuration (only active sensors are initialized)
SENSORS = [
    {"analog": ADS.P0, "digital": 14, "active": True},  # Sensor 1
    {"analog": ADS.P1, "digital": 15, "active": True},  # Sensor 2
    {"analog": ADS.P2, "digital": 18, "active": True},  # Sensor 3
    {"analog": ADS.P3, "digital": 23, "active": True},  # Sensor 4
]

ADDR_PIN = 7  # GPIO7 for address configuration
ALRT_PIN = 0  # GPIO0 for alerts

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(ADDR_PIN, GPIO.OUT)
GPIO.setup(ALRT_PIN, GPIO.IN)
for sensor in SENSORS:
    if sensor["active"]:
        GPIO.setup(sensor["digital"], GPIO.IN)

# Global SQLite connection
conn = None

# Retry logic for sensor reading
MAX_RETRIES = 3
def read_sensor_with_retries(sensor):
    for attempt in range(MAX_RETRIES):
        try:
            return read_sensor_channel(sensor)
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1}: Retrying sensor read for {sensor['analog']} due to error: {e}")
            time.sleep(1)  # Small delay between retries
    logging.error(f"Failed to read sensor {sensor['analog']} after {MAX_RETRIES} retries.")
    return 0, 0, "Error"

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    print("Received shutdown signal...")
    GPIO.cleanup()
    logging.info("GPIO Cleanup Done.")
    if conn:
        conn.close()
    api_process.terminate()  # Terminate the API subprocess
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

def setup_database():
    """Create or update SQLite table with sensor ID column."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moisture_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sensor_id INTEGER,
            moisture_level REAL,
            digital_status TEXT
        )
    """)
    conn.commit()

def save_to_database(sensor_id, moisture_level, digital_status):
    """Save sensor data to SQLite."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO moisture_data (sensor_id, moisture_level, digital_status)
            VALUES (?, ?, ?)
        """, (sensor_id, moisture_level, digital_status))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")

def convert_adc_to_moisture(adc_value):
    """Convert raw ADC value to moisture percentage."""
    min_adc = 14000
    max_adc = 26000
    moisture_level = ((max_adc - adc_value) / (max_adc - min_adc)) * 100
    return max(0, min(100, moisture_level))

def read_sensor_channel(sensor):
    """Read data from a single sensor channel."""
    try:
        chan = AnalogIn(ads, sensor["analog"])
        adc_value = chan.value
        if adc_value == 0 or adc_value > 32767:  # Handle disconnected or floating pins
            logging.warning(f"Sensor channel {sensor['analog']} may be disconnected.")
            return adc_value, 0, "Disconnected"
        moisture_level = convert_adc_to_moisture(adc_value)
        digital_status = "Dry" if GPIO.input(sensor["digital"]) == GPIO.HIGH else "Wet"
        return adc_value, moisture_level, digital_status
    except OSError as e:
        logging.error(f"I2C error on sensor channel {sensor['analog']}: {e}")
        return 0, 0, "Error"
    except Exception as e:
        logging.error(f"Unexpected error on sensor channel {sensor['analog']}: {e}")
        return 0, 0, "Error"

def read_sensors():
    """Read data from all active sensors via ADS1115 and GPIO."""
    for index, sensor in enumerate(SENSORS, start=1):
        if not sensor["active"]:
            continue

        adc_value, moisture_level, digital_status = read_sensor_with_retries(sensor)
        print(f"Sensor {index} - Raw ADC Value: {adc_value}, Moisture Level: {moisture_level:.2f}%, Digital Status: {digital_status}")
        logging.info(f"Sensor {index} - Raw ADC Value: {adc_value}, Moisture Level: {moisture_level:.2f}%, Digital Status: {digital_status}")
        save_to_database(index, moisture_level, digital_status)

    if GPIO.input(ALRT_PIN) == GPIO.HIGH:
        print("Alert! Check sensor readings.")
        logging.warning("Alert triggered on ALRT_PIN.")

def manage_data_retention():
    """Delete records older than the retention period."""
    try:
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM moisture_data WHERE timestamp < ?
        """, (cutoff_date.strftime("%Y-%m-%d %H:%M:%S"),))
        conn.commit()
        logging.info(f"Old data deleted up to {cutoff_date}.")
    except sqlite3.Error as e:
        logging.error(f"Data retention error: {e}")

def sensor_health_check():
    """Monitor sensors for consistent or missing values."""
    try:
        cursor = conn.cursor()
        for sensor_id in range(1, len(SENSORS) + 1):
            if not SENSORS[sensor_id - 1]["active"]:
                continue

            cursor.execute("""
                SELECT AVG(moisture_level) FROM moisture_data WHERE sensor_id = ?
            """, (sensor_id,))
            avg_moisture = cursor.fetchone()[0]
            if avg_moisture is None:
                logging.warning(f"No data recorded for Sensor {sensor_id}.")
            elif avg_moisture < 10:
                logging.warning(f"Low average moisture level for Sensor {sensor_id}: {avg_moisture:.2f}%")
    except sqlite3.Error as e:
        logging.error(f"Health check error: {e}")

def main():
    """Main function to read sensors and store data in SQLite."""
    global conn
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to the database: {e}")
        sys.exit(1)
    setup_database()
    print("Starting Multi-Sensor Plant Monitoring...")
    GPIO.output(ADDR_PIN, GPIO.HIGH)

    while True:
        read_sensors()
        manage_data_retention()
        sensor_health_check()
        time.sleep(READ_INTERVAL)

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
