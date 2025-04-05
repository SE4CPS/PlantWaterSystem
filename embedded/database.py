"""
database.py – SQLite helpers

• One connection **per request**  ➜  no “connection already closed” errors.
• `pool_pre_ping` etc. are not needed for SQLite, we just open/close fast.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends

from config import DB_NAME, DATA_RETENTION_DAYS   # e.g. DB_NAME = "sproutly.db"

log = logging.getLogger(__name__)
_DB_PATH = Path(DB_NAME).expanduser().resolve()


# ──────────────────────────────────────────────────────────────────────────
# 1.  One‑time setup  (called from main.py / app startup)
# ──────────────────────────────────────────────────────────────────────────
def setup_database() -> None:
    """Create the table (if missing) and run any ALTERs for backward‑compat."""
    with sqlite3.connect(_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS moisture_data (
                id              INTEGER PRIMARY KEY,        -- readingid (unique)
                timestamp       TEXT    DEFAULT CURRENT_TIMESTAMP,
                device_id       TEXT,
                sensor_id       INTEGER,
                adc_value       REAL,
                moisture_level  REAL,
                digital_status  TEXT,
                weather_temp    REAL,
                weather_humidity REAL,
                weather_sunlight REAL,
                weather_wind_speed REAL,
                location        TEXT,
                weather_fetched TEXT
            )
            """
        )
        conn.commit()

        # Any legacy columns you might still need to add
        legacy_cols = [
            ("device_id",        "TEXT"),
            ("adc_value",        "REAL"),
            ("location",         "TEXT"),
            ("weather_fetched",  "TEXT"),
        ]
        for col, col_type in legacy_cols:
            try:
                cursor.execute(f"ALTER TABLE moisture_data ADD COLUMN {col} {col_type}")
                conn.commit()
            except sqlite3.OperationalError:
                # Column already exists – ignore
                pass

        log.info("SQLite schema ready at %s", _DB_PATH)


# ──────────────────────────────────────────────────────────────────────────
# 2.  Request‑scoped connection dependency
# ──────────────────────────────────────────────────────────────────────────
def get_db():
    """
    FastAPI dependency:
        with sqlite3.connect() as conn:
            yield conn
    """
    conn = sqlite3.connect(_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────────────────
# 3.  Helper utilities
# ──────────────────────────────────────────────────────────────────────────
def save_record(conn: sqlite3.Connection, record: tuple) -> None:
    """
    Insert one row. The tuple order must match the column list below.
    Raises sqlite3.IntegrityError on duplicate `id`.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO moisture_data (
            id, timestamp, device_id, sensor_id, adc_value, moisture_level,
            digital_status, weather_temp, weather_humidity, weather_sunlight,
            weather_wind_speed, location, weather_fetched
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        record,
    )
    conn.commit()


def delete_old_records(conn: sqlite3.Connection) -> None:
    cutoff_date = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM moisture_data WHERE timestamp < ?",
        (cutoff_date.strftime("%Y-%m-%d %H:%M:%S"),),
    )
    conn.commit()
