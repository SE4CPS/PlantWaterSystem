from connection import DatabaseConnection

class SensorDataQueries:

    def create_table(self):
        """Creates the SensorsData table."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS SensorsData (
                        ReadingID SERIAL PRIMARY KEY,
                        SensorID INT NOT NULL,
                        SensorReading FLOAT(3) NOT NULL,
                        TimeCollected TIMESTAMP NOT NULL DEFAULT NOW(),
                        FOREIGN KEY (SensorID) REFERENCES Sensors(SensorID)
                    );
                """)
                conn.commit()
        finally:
            DatabaseConnection.release_connection(conn)

    def insert_sensor_data(self, sensor_id, sensor_reading):
        """Inserts a new sensor data reading."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO SensorsData (SensorID, SensorReading) VALUES (%s, %s) RETURNING ReadingID;", 
                            (sensor_id, sensor_reading))
                reading_id = cur.fetchone()[0]
                conn.commit()
                return reading_id
        finally:
            DatabaseConnection.release_connection(conn)

    def get_sensor_data(self, sensor_id):
        """Fetches all sensor data for a specific sensor."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM SensorsData WHERE SensorID = %s;", (sensor_id,))
                return cur.fetchall()
        finally:
            DatabaseConnection.release_connection(conn)
