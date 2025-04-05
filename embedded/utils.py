import os
import csv
import logging
from config import ENABLE_CSV_OUTPUT, CSV_FILENAME

def save_to_csv(record):
    if not ENABLE_CSV_OUTPUT:
        return
    file_exists = os.path.isfile(CSV_FILENAME)
    try:
        with open(CSV_FILENAME, mode="a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                header = ["timestamp (UTC)", "device_id", "sensor_id", "adc_value", "moisture_level", "digital_status",
                          "weather_temp", "weather_humidity", "weather_sunlight",
                          "weather_wind_speed", "location", "weather_fetched (UTC)"]
                writer.writerow(header)
            writer.writerow(record)
    except Exception as e:
        logging.error(f"Error writing to CSV file: {e}")
