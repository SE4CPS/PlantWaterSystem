#!/usr/bin/env python3

import sqlite3
from config import DB_NAME, DATA_RETENTION_DAYS
import logging
from datetime import datetime, timedelta

def setup_database(conn):
    """Creates the moisture_data table if it does not exist, adding columns for adc_value, location, and weather_fetched."""
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
    # Attempt to add columns if they don't exist (ignore errors if already present)
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

def save_record(conn, record):
    """
    Inserts a record into the moisture_data table.
    record should be a tuple:
      (sensor_id, adc_value, moisture_level, digital_status,
       weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
       location, weather_fetched)
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO moisture_data 
        (sensor_id, adc_value, moisture_level, digital_status,
         weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
         location, weather_fetched)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, record)
    conn.commit()

def delete_old_records(conn):
    """Deletes records older than DATA_RETENTION_DAYS from the moisture_data table."""
    cutoff_date = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM moisture_data WHERE timestamp < ?",
                   (cutoff_date.strftime("%Y-%m-%d %H:%M:%S"),))
    conn.commit()
