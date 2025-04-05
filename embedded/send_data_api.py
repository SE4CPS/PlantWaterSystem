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

def _no_conversion(ts: str | None) -> str | None:
    # Return the timestamp exactly as stored (e.g. "2025-04-05 14:31:50")
    return ts

def _sanitize_num(val):
    return 0 if val is None else val

def _sanitize_txt(val):
    return "" if val is None else val

def fetch_next_group(last_id: int) -> list[dict]:
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT timestamp, device_id, sensor_id, adc_value, moisture_level,
                   digital_status, weather_temp, weather_humidity,
                   weather_sunlight, weather_wind_speed, location, weather_fetched, id
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
        ts, device_id, sensor_id, adc_val, moist_lvl, dig_status, w_temp, w_hum, w_sun, w_wind, loc, w_fetch, r_id = row
        groups[ts].append({
            "timestamp": _no_conversion(ts),
            "device_id": device_id,
            "sensor_id": sensor_id,
            "adc_value": _sanitize_num(adc_val),
            "moisture_level": round(_sanitize_num(moist_lvl), 2),
            "digital_status": _sanitize_txt(dig_status),
            "weather_temp": _sanitize_num(w_temp),
            "weather_humidity": _sanitize_num(w_hum),
            "weather_sunlight": _sanitize_num(w_sun),
            "weather_wind_speed": _sanitize_num(w_wind),
            "location": _sanitize_txt(loc),
            "weather_fetched": _no_conversion(w_fetch),
            "id": r_id,
        })

    for ts in sorted(groups.keys()):
        group = groups[ts]
        if len(group) == 4 and len({g["sensor_id"] for g in group}) == 4:
            return group
    return []

def send_one_reading(url: str, reading: dict) -> (bool, bool):
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
    global LAST_SENT_ID
    group = fetch_next_group(LAST_SENT_ID)
    if not group:
        logging.info("No complete group to send.")
        return True

    max_id = max(r["id"] for r in group)
    for reading in group:
        def attempt_send():
            return send_one_reading(url, reading)
        success, duplicate = retry_with_backoff(attempt_send)
        if not (success or duplicate):
            return False
    LAST_SENT_ID = max_id
    return True

def send_all_available(url: str) -> bool:
    while True:
        group = fetch_next_group(LAST_SENT_ID)
        if not group:
            return True
        if not send_next_group(url):
            return False

def get_min_id_after_timestamp(ts_str: str) -> int | None:
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT MIN(id) FROM moisture_data WHERE timestamp > ?", (ts_str,))
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return row[0]
        return None
    except Exception as e:
        logging.error(f"get_min_id_after_timestamp error: {e}")
        return None

@app.route("/send-data", methods=["POST"])
def auto_send():
    req = request.get_json() or {}
    after = req.get("after")
    if after:
        new_min = get_min_id_after_timestamp(after)
        if new_min is not None:
            global LAST_SENT_ID
            LAST_SENT_ID = new_min - 1
            logging.info(f"Auto-send reset: LAST_SENT_ID set to {LAST_SENT_ID}")
    ok = send_all_available(BACKEND_API_SEND_DATA)
    if ok:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

@app.route("/send-current", methods=["POST"])
def manual_send():
    req = request.get_json() or {}
    after = req.get("after")
    if after:
        new_min = get_min_id_after_timestamp(after)
        if new_min is not None:
            global LAST_SENT_ID
            LAST_SENT_ID = new_min - 1
            logging.info(f"Manual reset: LAST_SENT_ID set to {LAST_SENT_ID}")
    ok = send_all_available(BACKEND_API_SEND_CURRENT)
    if ok:
        return jsonify({"message": "Current data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

def _scheduled_job():
    send_all_available(BACKEND_API_SEND_DATA)

def _start_scheduler():
    import schedule
    schedule.every(SENSOR_READ_INTERVAL).seconds.do(_scheduled_job)
    logging.info(f"Scheduler started: interval = {SENSOR_READ_INTERVAL} seconds.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=_start_scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, debug=False)
