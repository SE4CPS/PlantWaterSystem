from flask import Flask, jsonify, request
import sqlite3, schedule, time, threading, logging, os, json, requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import (
    DB_NAME,
    BACKEND_API_SEND_DATA,
    BACKEND_API_SEND_CURRENT,
    RETRY_ATTEMPTS,
    BASE_DELAY,
    SENSOR_READ_INTERVAL,
)

# ────────────────────────── logging ────────────────────────────
logging.basicConfig(
    filename="api_log.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = Flask(__name__)
# LAST_SENT_TIMESTAMP is stored as the original local timestamp string (e.g. "2025-04-05 08:37:04")
LAST_SENT_TIMESTAMP: str | None = None

# ───────────────────── helper / utility code ─────────────────────

def _to_utc_iso(sql_dt: str | None) -> str | None:
    """
    Convert a naive datetime string from the local DB (assumed to be in
    America/Los_Angeles time) to an ISO‑8601 UTC string.
    Example: "2025-04-05 04:40:17" → "2025-04-05T11:40:17Z" (if PDT, UTC‑7)
    """
    if not sql_dt:
        return None
    try:
        local_dt = datetime.strptime(sql_dt, "%Y-%m-%d %H:%M:%S")
        local_dt = local_dt.replace(tzinfo=ZoneInfo("America/Los_Angeles"))
        utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
        return utc_dt.isoformat().replace("+00:00", "Z")
    except ValueError:
        return sql_dt

def _sanitize_number(val):
    return 0 if val is None else val

def _sanitize_text(val):
    return "" if val is None else val

def _generate_unique_id(sensor_id: int) -> int:
    """
    Generate a unique positive integer based on the current epoch milliseconds
    plus the sensor_id. This avoids duplicate key errors at the backend.
    """
    epoch_ms = int(time.time() * 1000)
    return epoch_ms + sensor_id

def fetch_recent_data(after_sql: str):
    """
    Retrieve rows from the local DB with timestamp > after_sql.
    For each record, include the original local timestamp (key "local_ts")
    and convert the timestamp to proper UTC ISO‑8601 (key "timestamp") for sending.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                timestamp,
                sensor_id,
                adc_value,
                moisture_level,
                digital_status,
                weather_temp,
                weather_humidity,
                weather_sunlight,
                weather_wind_speed,
                location,
                weather_fetched,
                device_id
            FROM moisture_data
            WHERE timestamp > ?
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
    for r in rows:
        local_ts = r[0]  # original local DB timestamp (e.g., "2025-04-05 04:40:17")
        sensor_id = r[1]
        record = {
            # Generate a new unique id for the payload
            "id": _generate_unique_id(sensor_id if sensor_id else 0),
            # Send the UTC-converted timestamp
            "timestamp": _to_utc_iso(local_ts),
            # Also include the original local timestamp for internal tracking
            "local_ts": local_ts,
            "sensor_id": sensor_id,
            "adc_value": _sanitize_number(r[2]),
            "moisture_level": round(_sanitize_number(r[3]), 2),
            "digital_status": _sanitize_text(r[4]),
            "weather_temp": _sanitize_number(r[5]),
            "weather_humidity": _sanitize_number(r[6]),
            "weather_sunlight": _sanitize_number(r[7]),
            "weather_wind_speed": _sanitize_number(r[8]),
            "location": _sanitize_text(r[9]),
            # For weather_fetched, if missing, fallback to local_ts
            "weather_fetched": _to_utc_iso(r[10]) or _to_utc_iso(local_ts),
            "device_id": _sanitize_text(r[11]),
        }
        records.append(record)
    return records

def send_request(url: str, data: list[dict]) -> bool:
    """
    POST the payload (with key "data") to the backend.
    Logs the response on errors.
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
        logging.error(f"Retrying after {delay} s…")
        time.sleep(delay)
    logging.error("All retry attempts failed.")
    return False

def send_data_to_backend(url: str, after: str | None = None):
    """
    Fetch new rows from the local DB (using local timestamps) and POST them
    to the backend. LAST_SENT_TIMESTAMP is stored as a local timestamp string.
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

    ok = retry_with_backoff(lambda: send_request(url, data))
    return ok, data if ok else None

# ───────────────────────────── routes ─────────────────────────────

@app.route("/send-current", methods=["POST"])
def send_current():
    ok, data = send_data_to_backend(BACKEND_API_SEND_CURRENT, after=LAST_SENT_TIMESTAMP)
    if data:
        # Update LAST_SENT_TIMESTAMP using the highest local_ts value from the payload.
        LAST_SENT_TIMESTAMP = max(rec["local_ts"] for rec in data)
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
        LAST_SENT_TIMESTAMP = max(rec["local_ts"] for rec in data)
    return (
        jsonify({"message": "Manual data sent successfully" if ok else "Failed to send manual data"}),
        200 if ok else 500,
    )

@app.route("/send-data", methods=["POST"])
def auto_send():
    ok, data = send_data_to_backend(BACKEND_API_SEND_DATA)
    if data:
        LAST_SENT_TIMESTAMP = max(rec["local_ts"] for rec in data)
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
