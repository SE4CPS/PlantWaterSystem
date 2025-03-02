import sqlite3
from config import DB_NAME, DATA_RETENTION_DAYS
import logging
from datetime import datetime, timedelta

def setup_database(conn):
    cursor = conn.cursor()
    # Table with device_id placed before sensor_id in logical order
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moisture_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            device_id TEXT,
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
        cursor.execute("ALTER TABLE moisture_data ADD COLUMN device_id TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
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
    # Record order: (device_id, sensor_id, adc_value, moisture_level, digital_status,
    # weather_temp, weather_humidity, weather_sunlight, weather_wind_speed, location, weather_fetched)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO moisture_data 
        (device_id, sensor_id, adc_value, moisture_level, digital_status,
         weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
         location, weather_fetched)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, record)
    conn.commit()

def delete_old_records(conn):
    cutoff_date = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM moisture_data WHERE timestamp < ?",
                   (cutoff_date.strftime("%Y-%m-%d %H:%M:%S"),))
    conn.commit()
