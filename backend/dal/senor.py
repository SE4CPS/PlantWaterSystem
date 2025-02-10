from connection import DatabaseConnection

class SensorQueries:

    def create_table(self):
        """Creates the Sensors table."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS Sensors (
                        SensorID SERIAL PRIMARY KEY,
                        SensorStatus VARCHAR(3) CHECK (SensorStatus IN ('ON', 'OFF')),
                        PlantID INT NOT NULL,
                        FOREIGN KEY (PlantID) REFERENCES Plant(PlantID)
                    );
                """)
                conn.commit()
        finally:
            DatabaseConnection.release_connection(conn)

    def insert_sensor(self, sensor_status, plant_id):
        """Inserts a new sensor record."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO Sensors (SensorStatus, PlantID) VALUES (%s, %s) RETURNING SensorID;", 
                            (sensor_status, plant_id))
                sensor_id = cur.fetchone()[0]
                conn.commit()
                return sensor_id
        finally:
            DatabaseConnection.release_connection(conn)

    def update_sensor(self, sensor_id, sensor_status):
        """Updates a sensor record by ID."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE Sensors SET SensorStatus = %s WHERE SensorID = %s RETURNING SensorID;", 
                            (sensor_status, sensor_id))
                updated_id = cur.fetchone()
                conn.commit()
                return updated_id is not None
        finally:
            DatabaseConnection.release_connection(conn)

    def delete_sensor(self, sensor_id):
        """Deletes a sensor record by ID."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM Sensors WHERE SensorID = %s RETURNING SensorID;", (sensor_id,))
                deleted_id = cur.fetchone()
                conn.commit()
                return deleted_id is not None
        finally:
            DatabaseConnection.release_connection(conn)
