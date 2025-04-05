from flask import Flask, jsonify, request
import sqlite3, schedule, time, threading, logging, os, requests
from collections import defaultdict
from config import (
    DB_NAME,
    BACKEND_API_SEND_DATA,
    BACKEND_API_SEND_CURRENT,
    RETRY_ATTEMPTS,
    BASE_DELAY,
    SENSOR_READ_INTERVAL,
)

logging.basicConfig(
    filename="api_log.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = Flask(__name__)

# Global pointer: the last DB id that has been sent (or skipped)
LAST_SENT_ID = 0

# ───────────────────────── Helper Functions ─────────────────────────

def _no_conversion(ts: str | None) -> str | None:
    """
    Return the timestamp as stored in the DB (a simple "YYYY-MM-DD HH:MM:SS" string)
    without any conversion.
    """
    return ts

def _sanitize_num(val):
    return 0 if val is None else val

def _sanitize_txt(val):
    return "" if val is None else val

def fetch_next_group(last_id: int) -> list[dict]:
    """
    Fetch rows from the moisture_data table with id > last_id.
    Group them by the 'timestamp' field.
    Return the first group that has exactly 4 rows (one per sensor with distinct sensor_id).
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, timestamp, sensor_id, adc_value, moisture_level,
                   digital_status, weather_temp, weather_humidity,
                   weather_sunlight, weather_wind_speed,
                   location, weather_fetched, device_id
            FROM moisture_data
            WHERE id > ?
            ORDER BY id ASC
            """,
            (last_id,),
        )
        rows = cur.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database query error: {e}")
        return []
    finally:
        conn.close()

    if not rows:
        return []

    groups = defaultdict(list)
    for row in rows:
        r_id, ts, sensor_id, adc_val, moist_lvl, dig_status, w_temp, w_hum, w_sun, w_wind, loc, w_fetch, dev_id = row
        groups[ts].append({
            "id": r_id,
            "timestamp": ts,  # Stored as simple "YYYY-MM-DD HH:MM:SS"
            "sensor_id": sensor_id,
            "adc_value": _sanitize_num(adc_val),
            "moisture_level": round(_sanitize_num(moist_lvl), 2),
            "digital_status": _sanitize_txt(dig_status),
            "weather_temp": _sanitize_num(w_temp),
            "weather_humidity": _sanitize_num(w_hum),
            "weather_sunlight": _sanitize_num(w_sun),
            "weather_wind_speed": _sanitize_num(w_wind),
            "location": _sanitize_txt(loc),
            "weather_fetched": _no_conversion(w_fetch),  # as stored
            "device_id": _sanitize_txt(dev_id),
        })

    for ts in sorted(groups.keys()):
        group = groups[ts]
        if len(group) == 4 and len({r["sensor_id"] for r in group}) == 4:
            return group
    return []

def send_one_reading(url: str, reading: dict) -> (bool, bool):
    """
    Send a single reading as JSON.
    The payload wraps the reading in a top-level "data" key, whose value is a list.
    """
    payload = {
        "data": [
            {
                "id": reading["id"],
                "timestamp": _no_conversion(reading["timestamp"]),
                "device_id": reading["device_id"],
                "sensor_id": reading["sensor_id"],
                "adc_value": reading["adc_value"],
                "moisture_level": reading["moisture_level"],
                "digital_status": reading["digital_status"],
                "weather_temp": reading["weather_temp"],
                "weather_humidity": reading["weather_humidity"],
                "weather_sunlight": reading["weather_sunlight"],
                "weather_wind_speed": reading["weather_wind_speed"],
                "location": reading["location"],
                "weather_fetched": _no_conversion(reading["weather_fetched"]),
            }
        ]
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            logging.info(f"Reading {reading['id']} sent successfully.")
            return True, False
        else:
            txt = resp.text.lower()
            if "duplicate key" in txt or "already exists" in txt:
                logging.error(f"Duplicate key error for reading {reading['id']}: {resp.text}")
                return False, True
            logging.error(f"Backend returned {resp.status_code} for reading {reading['id']}: {resp.text}")
            return False, False
    except Exception as e:
        logging.error(f"HTTP send failed for reading {reading['id']}: {e}")
        return False, False

def retry_with_backoff(func, attempts=RETRY_ATTEMPTS, base=BASE_DELAY) -> (bool, bool):
    dup_flag = False
    for i in range(attempts):
        success, dup = func()
        if dup:
            dup_flag = True
        if success:
            return True, dup_flag
        delay = base * (2 ** i)
        logging.error(f"Retrying after {delay} s…")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False, dup_flag

def send_next_group(url: str) -> bool:
    """
    Fetch the next complete group of 4 readings (with identical timestamp)
    and send each reading individually.
    After processing, update LAST_SENT_ID to the max id in the group.
    """
    global LAST_SENT_ID
    group = fetch_next_group(LAST_SENT_ID)
    if not group:
        logging.info("No complete group to send.")
        return True

    max_id_in_group =_
