from flask import Flask, jsonify, request
import sqlite3
import schedule
import time
import threading
import logging
import os
import subprocess
import json
import tempfile
from datetime import datetime, timedelta
from config import (
    DB_NAME,
    BACKEND_API_SEND_DATA,
    BACKEND_API_SEND_CURRENT,
    RETRY_ATTEMPTS,
    BASE_DELAY,
    SENSOR_READ_INTERVAL,          # ← use the same cadence as sensor readings
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


def fetch_recent_data(after_sql: str):
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
                "adc_value": r[3],
                "moisture_level": round(r[4], 2),
                "digital_status": r[5],
                "weather_temp": r[6],
                "weather_humidity": r[7],
                "weather_sunlight": r[8],
                "weather_wind_speed": r[9],
                "location": r[10],
                "weather_fetched": _to_iso(r[11]),
                "device_id": r[12],
            }
        )
    return records


def send_request_curl(url: str, data: list[dict]) -> bool:
    payload = json.dumps({"data": data})
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write(payload)
        fname = tmp.name

    cmd = [
        "curl",
        "--location",
        "--silent",
        "--show-error",
        "--header",
        "Content-Type: application/json",
        "--data-binary",
        f"@{fname}",
        "--output",
        "/dev/null",
        "--write-out",
        "%{http_code}",
        url,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(fname)

    if res.returncode == 0 and res.stdout.strip() == "200":
        logging.info("Data sent successfully.")
        return True

    code_or_err = res.stdout.strip() if res.returncode == 0 else res.stderr
    logging.error(f"Curl send failed ({code_or_err})")
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

    ok = retry_with_backoff(lambda: send_request_curl(url, data))
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
    # run the job every SENSOR_READ_INTERVAL seconds (real‑time push)
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
