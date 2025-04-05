from flask import Flask, jsonify, request
import sqlite3, schedule, time, threading, logging, os, json, requests
from datetime import datetime, timedelta, timezone
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
LAST_SENT_TIMESTAMP: str | None = None  # “YYYY‑MM‑DD HH:MM:SS”

# ───────────────────── helper / utility code ─────────────────────

def _to_iso(sql_dt: str | None) -> str | None:
    """
    Convert a local time string 'YYYY-MM-DD HH:MM:SS' from the local DB into
    a proper ISO 8601 UTC timestamp.

    This function:
      1. Parses the local timestamp.
      2. Attaches the system's local timezone.
      3. Converts it to UTC.
      4. Formats it as ISO 8601 with a trailing 'Z'.
    """
    if not sql_dt:
        return None
    try:
        # Parse the naïve local time
        local_dt = datetime.strptime(sql_dt, "%Y-%m-%d %H:%M:%S")
        # Attach local timezone info (using the system's current timezone)
        local_tz = datetime.now().astimezone().tzinfo
        local_dt = local_dt.replace(tzinfo=local_tz)
        # Convert to UTC
        utc_dt = local_dt.astimezone(timezone.utc)
        return utc_dt.isoformat().replace("+00:00", "Z")
    except Exception as e:
        logging.error(f"_to_iso conversion error: {e}")
        return sql_dt

def _from_iso(iso_dt: str) -> str:
    """Convert 'YYYY‑MM‑DDTHH:MM:SSZ' back to 'YYYY‑MM‑DD HH:MM:SS'."""
    return iso_dt.replace("T", " ").rstrip("Z")

def _sanitize_number(val):
    return 0 if val is None else val

def _sanitize_text(val):
    return "" if val is None else val

# Define a base epoch (Jan 1, 2020) to reduce the size of the unique id value.
BASE_EPOCH = 1577836800  # Unix epoch seconds for 2020-01-01 00:00:00

def _generate_unique_id(sensor_id: int) -> int:
    """
    Generate a unique id based on the current epoch seconds relative to BASE_EPOCH.
    For example, in 2025 the difference is around 132,163,200 seconds.
    Multiply by 10 and add the sensor_id (assumed to be 1–4) to ensure uniqueness.
    This guarantees a value well within the 32‑bit signed integer range.
    """
    epoch_diff = int(time.time()) - BASE_EPOCH  # This is in seconds.
    return epoch_diff * 10 + sensor_id

def fetch_recent_data(after_sql: str):
    """
    Return rows newer than *after_sql* as a list of dicts.
    Converts None → 0 / "" so the backend never receives JSON nulls.
    Instead of sending the local DB's id, generate a new unique id.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT timestamp, sensor_id, adc_value, moisture_level,
                   digital_status, weather_temp, weather_humidity,
                   weather_sunlight, weather_wind_speed,
                   location, weather_fetched, device_id
            FROM   moisture_data
            WHERE  timestamp > ?
            """,
            (after_sql,),
        )
        rows = cur.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database connection/query error: {e}")
        return []
    finally:
        conn.close()

    records = []
    for row in rows:
        (
            local_ts,
            sensor_id,
            adc_val,
            moist_lvl,
            dig_status,
            w_temp,
            w_hum,
            w_sun,
            w_wind,
            loc,
            w_fetch,
            dev_id
        ) = row

        record = {
            "id":               _generate_unique_id(sensor_id if sensor_id else 0),
            "timestamp":        _to_iso(local_ts),
            "sensor_id":        sensor_id,
            "adc_value":        _sanitize_number(adc_val),
            "moisture_level":   round(_sanitize_number(moist_lvl), 2),
            "digital_status":   _sanitize_text(dig_status),
            "weather_temp":     _sanitize_number(w_temp),
            "weather_humidity": _sanitize_number(w_hum),
            "weather_sunlight": _sanitize_number(w_sun),
            "weather_wind_speed": _sanitize_number(w_wind),
            "location":         _sanitize_text(loc),
            "weather_fetched":  _to_iso(w_fetch) or _to_iso(local_ts),
            "device_id":        _sanitize_text(dev_id),
        }
        records.append(record)

    return records

def send_request(url: str, data: list[dict]) -> bool:
    """
    POST *data* to *url* using requests. HTTP 200 = success.
    Logs response body on errors for easier debugging.
    """
    try:
        resp = requests.post(url, json={"data": data}, timeout=15)
        if resp.status_code == 200:
            logging.info("Data sent successfully.")
            return True
        logging.error(f"Backend returned {resp.status_code}: {resp.text}")
        return False
    except Exception as e:
        logging.error(f"HTTP send failed: {e}")
        return False

def retry_with_backoff(func, attempts=RETRY_ATTEMPTS, base=BASE_DELAY):
    for n in range(attempts):
        if func():
            return True
        delay = base * (2 ** n)
        logging.error(f"Retrying after {delay} s…")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False

def send_data_to_backend(url: str, after: str | None = None):
    """
    Fetch rows newer than *after* (SQL style) and push them to *url*.
    Returns (success_bool, data_sent_or_None).
    """
    global LAST_SENT_TIMESTAMP

    try:
        provided = (
            datetime.strptime(after, "%Y-%m-%d %H:%M:%S")
            if after
            else datetime.now() - timedelta(seconds=SENSOR_READ_INTERVAL)
        )
    except Exception:
        provided = datetime.now() - timedelta(seconds=SENSOR_READ_INTERVAL)

    if LAST_SENT_TIMESTAMP:
        try:
            last_dt = datetime.strptime(LAST_SENT_TIMESTAMP, "%Y-%m-%d %H:%M:%S")
            provided = max(provided, last_dt)
        except Exception:
            pass

    after_sql = provided.strftime("%Y-%m-%d %H:%M:%S")
    data = fetch_recent_data(after_sql)

    if not data:
        logging.error("No new data to send.")
        return True, None

    success = retry_with_backoff(lambda: send_request(url, data))
    return success, data if success else None

# ───────────────────────────── routes ─────────────────────────────

@app.route("/send-current", methods=["POST"])
def send_current():
    ok, data = send_data_to_backend(BACKEND_API_SEND_CURRENT, after=LAST_SENT_TIMESTAMP)
    if data:
        LAST_SENT_TIMESTAMP = _from_iso(max(r["timestamp"] for r in data))
    return (
        jsonify({"message": "Current data sent successfully" if ok else "Failed to send current data"}),
        200 if ok else 500,
    )

@app.route("/manual", methods=["POST"])
def manual_send():
    req = request.get_json() or {}
    after = req.get("after")
    if not after:
        return jsonify({"message": "Missing 'after' timestamp in request"}), 400

    ok, data = send_data_to_backend(BACKEND_API_SEND_DATA, after=after)
    if data:
        LAST_SENT_TIMESTAMP = _from_iso(max(r["timestamp"] for r in data))
    return (
        jsonify({"message": "Manual data sent successfully" if ok else "Failed to send manual data"}),
        200 if ok else 500,
    )

@app.route("/send-data", methods=["POST"])
def auto_send():
    ok, data = send_data_to_backend(BACKEND_API_SEND_DATA)
    if data:
        LAST_SENT_TIMESTAMP = _from_iso(max(r["timestamp"] for r in data))
    return (
        jsonify({"message": "Data sent successfully" if ok else "Failed to send data"}),
        200 if ok else 500,
    )

# ───────────────────── scheduler thread ─────────────────────

def _scheduled_job():
    send_data_to_backend(BACKEND_API_SEND_DATA)

def _start_scheduler():
    schedule.every(SENSOR_READ_INTERVAL).seconds.do(_scheduled_job)
    logging.info(f"Scheduler started: pushing data every {SENSOR_READ_INTERVAL} seconds.")
    while True:
        schedule.run_pending()
        time.sleep(1)

# ───────────────────────────── main ───────────────────────────────

if __name__ == "__main__":
    threading.Thread(target=_start_scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, debug=False)
