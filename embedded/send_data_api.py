from flask import Flask, jsonify, request
import sqlite3, schedule, time, threading, logging, os, json, tempfile, requests
from datetime import datetime, timedelta
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
LAST_SENT_TIMESTAMP: str | None = None  # “YYYY‑MM‑DD HH:MM:SS”


# ───────────────────── helper / utility code ───────────────────
def _to_iso(sql_dt: str | None) -> str | None:
    if not sql_dt:
        return None
    try:
        return datetime.strptime(sql_dt, "%Y-%m-%d %H:%M:%S").isoformat() + "Z"
    except ValueError:
        return sql_dt


def _from_iso(iso_dt: str) -> str:
    return iso_dt.replace("T", " ").rstrip("Z")


def _sanitize_number(val):
    return 0 if val is None else val


def _sanitize_text(val):
    return "" if val is None else val


def fetch_recent_data(after_sql: str):
    """
    Return rows newer than *after_sql* as a list of dicts.
    Converts None → 0 / "" so the backend never receives JSON nulls.
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
    for r in rows:
        records.append(
            {
                "id": r[0],
                "timestamp": _to_iso(r[1]),
                "sensor_id": r[2],
                "adc_value": _sanitize_number(r[3]),
                "moisture_level": round(_sanitize_number(r[4]), 2),
                "digital_status": _sanitize_text(r[5]),
                "weather_temp": _sanitize_number(r[6]),
                "weather_humidity": _sanitize_number(r[7]),
                "weather_sunlight": _sanitize_number(r[8]),
                "weather_wind_speed": _sanitize_number(r[9]),
                "location": _sanitize_text(r[10]),
                "weather_fetched": _to_iso(r[11]) or _to_iso(r[1]),
                "device_id": _sanitize_text(r[12]),
            }
        )
    return records


def send_request(url: str, data: list[dict]) -> bool:
    """
    POST *data* to *url* using requests.  HTTP 200 = success.
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
        delay = base * (2**n)
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

    # Determine effective lower bound
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
    ok, data = send_data_to_backend(
        BACKEND_API_SEND_CURRENT, after=LAST_SENT_TIMESTAMP
    )
    if data:
        LAST_SENT_TIMESTAMP = _from_iso(max(rec["timestamp"] for rec in data))
    return (
        jsonify(
            {
                "message": "Current data sent successfully"
                if ok
                else "Failed to send current data"
            }
        ),
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
        LAST_SENT_TIMESTAMP = _from_iso(max(rec["timestamp"] for rec in data))
    return (
        jsonify(
            {
                "message": "Manual data sent successfully"
                if ok
                else "Failed to send manual data"
            }
        ),
        200 if ok else 500,
    )


@app.route("/send-data", methods=["POST"])
def auto_send():
    ok, data = send_data_to_backend(BACKEND_API_SEND_DATA)
    if data:
        LAST_SENT_TIMESTAMP = _from_iso(max(rec["timestamp"] for rec in data))
    return (
        jsonify(
            {
                "message": "Data sent successfully"
                if ok
                else "Failed to send data"
            }
        ),
        200 if ok else 500,
    )


# ───────────────────── scheduler thread ────────────────────
def _scheduled_job():
    send_data_to_backend(BACKEND_API_SEND_DATA)


def _start_scheduler():
    schedule.every(SENSOR_READ_INTERVAL).seconds.do(_scheduled_job)
    logging.info(
        f"Scheduler started: pushing data every {SENSOR_READ_INTERVAL} seconds."
    )
    while True:
        schedule.run_pending()
        time.sleep(1)


# ───────────────────────────── main ───────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=_start_scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, debug=False)
