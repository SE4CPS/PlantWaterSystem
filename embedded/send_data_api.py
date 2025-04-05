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

# Global pointer: the last local DB id that has been sent (or skipped)
LAST_SENT_ID = 0

# ───────────────────────── Helper Functions ─────────────────────────

# Since the DB now stores ISO‑8601 timestamps, we use identity functions:
def _to_iso(ts: str | None) -> str | None:
    return ts

def _sanitize_num(val):
    return 0 if val is None else val

def _sanitize_txt(val):
    return "" if val is None else val

def fetch_next_group(last_id: int) -> list[dict]:
    """
    Fetch rows from the moisture_data table with id > last_id.
    Group them by the timestamp field (which is now an ISO‑8601 string).
    Return the first group that has exactly 4 rows (one per sensor)
    with distinct sensor_id values. If none found, return an empty list.
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
            "timestamp": ts,  # Already ISO‑8601
            "sensor_id": sensor_id,
            "adc_value": _sanitize_num(adc_val),
            "moisture_level": round(_sanitize_num(moist_lvl), 2),
            "digital_status": _sanitize_txt(dig_status),
            "weather_temp": _sanitize_num(w_temp),
            "weather_humidity": _sanitize_num(w_hum),
            "weather_sunlight": _sanitize_num(w_sun),
            "weather_wind_speed": _sanitize_num(w_wind),
            "location": _sanitize_txt(loc),
            "weather_fetched": w_fetch,  # Already ISO‑8601
            "device_id": _sanitize_txt(dev_id),
        })

    for ts in sorted(groups.keys()):
        group = groups[ts]
        if len(group) == 4 and len({r["sensor_id"] for r in group}) == 4:
            return group
    return []

def send_one_reading(url: str, reading: dict) -> (bool, bool):
    """
    Send a single reading (a JSON object with top-level fields) via POST.
    Returns a tuple (success, duplicate_flag) where:
      - success is True if HTTP 200 is returned.
      - duplicate_flag is True if the response indicates the reading already exists.
    """
    payload = {
        "id": reading["id"],
        "timestamp": reading["timestamp"],
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
        "weather_fetched": reading["weather_fetched"],
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            logging.info(f"Reading {reading['id']} sent successfully.")
            return True, False
        else:
            resp_text = resp.text.lower()
            if "duplicate key" in resp_text or "already exists" in resp_text:
                logging.error(f"Duplicate key error for reading {reading['id']}: {resp.text}")
                return False, True
            logging.error(f"Backend returned {resp.status_code} for reading {reading['id']}: {resp.text}")
            return False, False
    except Exception as e:
        logging.error(f"HTTP send failed for reading {reading['id']}: {e}")
        return False, False

def retry_with_backoff(func, attempts=RETRY_ATTEMPTS, base=BASE_DELAY) -> (bool, bool):
    """
    Retry the provided function with exponential backoff.
    Returns (final_success, duplicate_flag).
    """
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
    Fetch the next complete group of 4 readings (all having the same timestamp)
    and send each reading as a separate POST request.
    If any reading fails (other than due to a duplicate error), stop and return False.
    If a duplicate key error is encountered, treat that reading as already sent.
    Update LAST_SENT_ID to the maximum id in the group once done.
    """
    global LAST_SENT_ID
    group = fetch_next_group(LAST_SENT_ID)
    if not group:
        logging.info("No complete group to send.")
        return True

    max_id_in_group = max(r["id"] for r in group)
    for reading in group:
        def attempt_send():
            return send_one_reading(url, reading)
        success, duplicate = retry_with_backoff(attempt_send)
        if not (success or duplicate):
            # If any reading fails (and it's not a duplicate), stop sending this group.
            return False
    LAST_SENT_ID = max_id_in_group
    return True

def send_all_available(url: str) -> bool:
    """
    Keep sending complete groups (of 4 readings each) until no more groups are available.
    Returns True if all available groups have been sent (or skipped due to duplicates),
    or False if any group fails.
    """
    while True:
        group = fetch_next_group(LAST_SENT_ID)
        if not group:
            return True
        result = send_next_group(url)
        if not result:
            return False

# ───────────────────────────── Routes ─────────────────────────────

@app.route("/send-data", methods=["POST"])
def auto_send():
    # Auto-send uses BACKEND_API_SEND_DATA
    success = send_all_available(BACKEND_API_SEND_DATA)
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

@app.route("/send-current", methods=["POST"])
def manual_send():
    # Manual send uses BACKEND_API_SEND_CURRENT.
    # Optionally, a JSON payload with {"after": "YYYY-MM-DD HH:MM:SS"} can reset LAST_SENT_ID.
    req = request.get_json() or {}
    after_str = req.get("after")
    if after_str:
        new_min = get_min_id_after_timestamp(after_str)
        if new_min is not None:
            global LAST_SENT_ID
            LAST_SENT_ID = new_min - 1
            logging.info(f"Manual reset: LAST_SENT_ID set to {LAST_SENT_ID}")
    success = send_all_available(BACKEND_API_SEND_CURRENT)
    if success:
        return jsonify({"message": "Current data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

def get_min_id_after_timestamp(ts_str: str) -> int | None:
    """
    Return the minimum id in moisture_data where timestamp > ts_str.
    Assumes timestamps are stored as ISO‑8601 strings.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT MIN(id) FROM moisture_data
            WHERE timestamp > ?
            """,
            (ts_str,),
        )
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return row[0]
        return None
    except Exception as e:
        logging.error(f"get_min_id_after_timestamp error: {e}")
        return None

# ───────────────────── Scheduler Thread ─────────────────────

def _scheduled_job():
    send_all_available(BACKEND_API_SEND_DATA)

def _start_scheduler():
    schedule.every(SENSOR_READ_INTERVAL).seconds.do(_scheduled_job)
    logging.info(f"Scheduler started: interval = {SENSOR_READ_INTERVAL} seconds.")
    while True:
        schedule.run_pending()
        time.sleep(1)

# ───────────────────────────── Main ─────────────────────────────

if __name__ == "__main__":
    threading.Thread(target=_start_scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, debug=False)
