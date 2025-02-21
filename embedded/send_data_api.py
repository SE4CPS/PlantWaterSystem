import sqlite3
import datetime

# Database initialization
def initialize_db():
    conn = sqlite3.connect("plant_data.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_readings (
        ReadingId INTEGER PRIMARY KEY AUTOINCREMENT,
        SensorId INTEGER,
        SensorReading REAL,
        TimeCollected TEXT,
        DigitalStatus TEXT
    );
    """)
    conn.commit()
    conn.close()

# Read sensor data from log
def read_sensor_data_from_log(log_file):
    sensor_data = []
    try:
        with open(log_file, "r") as file:
            for line in file:
                if ',' in line:
                    try:
                        parts = line.strip().split(",")
                        sensor_id = int(parts[0])
                        moisture = float(parts[1])
                        status = parts[2]
                        sensor_data.append((sensor_id, moisture, status))
                    except (ValueError, IndexError):
                        print(f"Skipping malformed line: {line.strip()}")
        return sensor_data
    except FileNotFoundError:
        print(f"Log file {log_file} not found.")
        return []

# Insert data into database
def insert_sensor_data(sensor_id, reading, status):
    try:
        conn = sqlite3.connect("plant_data.db")
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO sensor_readings (SensorId, SensorReading, TimeCollected, DigitalStatus)
        VALUES (?, ?, ?, ?)
        """, (sensor_id, reading, timestamp, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to insert data: {e}")

# Fetch data for website display
def fetch_latest_sensor_data():
    conn = sqlite3.connect("plant_data.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT ReadingId, SensorId, SensorReading, TimeCollected, DigitalStatus
    FROM sensor_readings
    ORDER BY TimeCollected DESC
    LIMIT 10
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# Main function
def main():
    initialize_db()
    log_file = "sensor_log.log"
    sensor_data = read_sensor_data_from_log(log_file)

    if sensor_data:
        for sensor_id, reading, status in sensor_data:
            print(f"Inserting: Sensor {sensor_id}, Moisture {reading}%, Status {status}")
            insert_sensor_data(sensor_id, reading, status)

    print("Latest Sensor Data for Website:")
    latest_data = fetch_latest_sensor_data()
    for row in latest_data:
        print(row)

if __name__ == "__main__":
    main()
