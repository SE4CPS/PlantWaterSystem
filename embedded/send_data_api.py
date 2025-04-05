from flask import Flask, jsonify, request
import sqlite3, schedule, time, threading, logging, os, requests
from datetime import datetime, timedelta, timezone
from config import (
    DB_NAME,
    BACKEND_API_SEND_DATA,
    BACKEND_API_SEND_CURRENT,
    RETRY_ATTEMPTS,
    BASE_DELAY,
    SENSOR_READ_INTERVAL,
)

# Configure logging
logging.basicConfig(
    filename="api_log.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = Flask(__name__)

# Global pointer: last local DB id successfully (or skipped) sent
LAST_SENT_ID = 0

# ───────────────────────── Helper Functions ─────────────────────────

def _to_iso(sql_dt: str | None) -> str | None:
    """
    Convert a local time string 'YYYY-MM-DD HH:MM:SS' (assumed in local time)
    into an ISO 8601 UTC string.
    """
    if not sql_dt:
        return None
    try:
        # Parse the naïve local time
        local_dt = datetime.strptime(sql_dt, "%Y-%m-%d %H:%M:%S")
        # Attach local timezone info (system's current timezone)
        local_tz = datetime.now().astimezone().tzinfo
        local_dt = local_dt.replace(tzinfo=local_tz)
        # Convert to UTC
        utc_dt = local_dt.astimezone(timezone.utc)
        return utc_dt.isoformat().replace("+00:00", "Z")
    except Exception as e:
        logging.error(f"_to_iso conversion error: {e}")
        return sql_dt

def _sanitize_number(val):
    return 0 if val is None else val

def _sanitize_text(val):
    return "" if val is None else val

def fetch_next_group(last_sent_id: int) -> list[dict]:
    """
    Fetch rows from the local DB with id > last_sent_id.
    Then group them by their timestamp (assumed identical for one sensor read cycle).
    Return the first group that has exactly 4 rows (one reading per sensor)
    and where the sensor_ids are unique (ideally {1,2,3,4}). If none found, return [].
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
            (last_sent_id,),
        )
        rows = cur.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database connection/query error: {e}")
        return []
    finally:
        conn.close()

    if not rows:
        return []

    # Group rows by the timestamp string.
    groups = {}
    for row in rows:
        # row structure: (id, timestamp, sensor_id, adc_value, moisture_level, digital_status,
        #                 weather_temp, weather_humidity, weather_sunlight, weather_wind_speed,
        #                 location, weather_fetched, device_id)
        r_id, ts, sensor_id, adc_val, moist_lvl, dig_status, w_temp, w_hum, w_sun, w_wind, loc, w_fetch, dev_id = row
        groups.setdefault(ts, []).append({
            "id": r_id,
            "timestamp": _to_iso(ts),
            "sensor_id": sensor_id,
            "adc_value": _sanitize_number(adc_val),
            "moisture_level": round(_sanitize_number(moist_lvl), 2),
            "digital_status": _sanitize_text(dig_status),
            "weather_temp": _sanitize_number(w_temp),
            "weather_humidity": _sanitize_number(w_hum),
            "weather_sunlight": _sanitize_number(w_sun),
            "weather_wind_speed": _sanitize_number(w_wind),
            "location": _sanitize_text(loc),
            "weather_fetched": _to_iso(w_fetch) or _to_iso(ts),
            "device_id": _sanitize_text(dev_id),
        })

    # Process groups in order of timestamp
    for ts in sorted(groups.keys()):
        group = groups[ts]
        # We want exactly 4 readings and unique sensor_id values.
        if len(group) == 4 and len({r["sensor_id"] for r in group}) == 4:
            return group
    return []

def send_request(url: str, data: list[dict]) -> (bool, bool):
    """
    POST the data to the given URL.
    Returns (success, duplicate_flag) where:
      - success is True if HTTP 200 is received.
      - duplicate_flag is True if the response text indicates a duplicate key error.
    """
    try:
        resp = requests.post(url, json={"data": data}, timeout=15)
        if resp.status_code == 200:
            logging.info("Data sent successfully.")
            return True, False
        else:
            # Check if duplicate key error is in the response text.
            resp_text = resp.text.lower()
            if "duplicate key" in resp_text:
                logging.error(f"Duplicate key error: {resp.text}")
                return False, True
            logging.error(f"Backend returned {resp.status_code}: {resp.text}")
            return False, False
    except Exception as e:
        logging.error(f"HTTP send failed: {e}")
        return False, False

def retry_with_backoff(func, attempts=RETRY_ATTEMPTS, base=BASE_DELAY) -> (bool, bool):
    """
    Retry the provided function with exponential backoff.
    Returns (True, duplicate_flag) if it eventually succeeds,
    or (False, duplicate_flag) if it fails. The duplicate_flag is set if any attempt
    reported a duplicate key error.
    """
    duplicate_flag = False
    for n in range(attempts):
        success, dup = func()
        if dup:
            duplicate_flag = True
        if success:
            return True, duplicate_flag
        delay = base * (2 ** n)
        logging.error(f"Retrying after {delay} s…")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False, duplicate_flag

def send_next_group(url: str) -> bool:
    """
    Fetch the next complete group (4 readings with the same timestamp) and
    send it to the specified URL.
    If the send is successful (or if a duplicate key error indicates the data already exists),
    update LAST_SENT_ID to the maximum id in that group.
    Returns True if the group was sent or skipped; False otherwise.
    """
    global LAST_SENT_ID
    group = fetch_next_group(LAST_SENT_ID)
    if not group:
        logging.info("No complete group to send.")
        return True  # Nothing to send is not an error.

    def attempt_send():
        return send_request(url, group)

    success, duplicate = retry_with_backoff(attempt_send)
    # Whether successful or duplicate error, update LAST_SENT_ID to skip this group.
    new_last_id = max(r["id"] for r in group)
    LAST_SENT_ID = new_last_id
    if success or duplicate:
        return True
    return False

# ───────────────────────────── Routes ─────────────────────────────

@app.route("/send-data", methods=["POST"])
def auto_send():
    # Auto-send uses the BACKEND_API_SEND_DATA endpoint.
    success = send_next_group(BACKEND_API_SEND_DATA)
    if success:
        return jsonify({"message": "Data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send data"}), 500

@app.route("/send-current", methods=["POST"])
def manual_send():
    # Manual send uses the BACKEND_API_SEND_CURRENT endpoint.
    success = send_next_group(BACKEND_API_SEND_CURRENT)
    if success:
        return jsonify({"message": "Current data sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send current data"}), 500

# ───────────────────── Scheduler Thread ─────────────────────

def _scheduled_job():
    send_next_group(BACKEND_API_SEND_DATA)

def _start_scheduler():
    schedule.every(SENSOR_READ_INTERVAL).seconds.do(_scheduled_job)
    logging.info(f"Scheduler started: pushing data every {SENSOR_READ_INTERVAL} seconds.")
    while True:
        schedule.run_pending()
        time.sleep(1)

# ───────────────────────────── Main ─────────────────────────────

if __name__ == "__main__":
    threading.Thread(target=_start_scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, debug=False)
