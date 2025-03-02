from config.database import get_connection, release_connection
from schemas.sensor_schema import MoistureDataSchema
import psycopg2 
from psycopg2 import  DatabaseError, IntegrityError

class SensorDAL:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def receive_moisture_data(self, sensor: MoistureDataSchema):
        try:
            # Validate input data
            if not sensor.sensor_id or not sensor.timestamp:
                raise ValueError("Invalid input data: Missing sensor_id or timestamp")

            if not isinstance(sensor.moisture_level, (int, float)) or not (0 <= sensor.moisture_level <= 100):
                raise ValueError("Invalid input data: Moisture level must be a number between 0 and 100")

            if sensor.digital_status not in ["Wet", "Dry"]:
                raise ValueError("Invalid input data: Digital status must be 'Wet' or 'Dry'")

            # Execute the query to insert the plant data
            self.cursor.execute("""
                INSERT INTO sensor (sensor_id, id, timestamp, moisture_level, digital_status)
                VALUES (%s, %s, %s, %s, %s) RETURNING sensor_id, id;
            """, (sensor.sensor_id, sensor.id, sensor.timestamp, sensor.moisture_level, sensor.digital_status))

            # Commit the transaction
            self.conn.commit()

            # Get the returned sensor_id
            returned_sensor_id, returned_id = self.cursor.fetchone()

            # Return the response in JSON format
            return {
                "status": "success",
                "SensorID": sensor.sensor_id,
                "RowID": sensor.id,
                "TimeStamp": sensor.timestamp,
                "Moisture": sensor.moisture_level,
                "PlantStatus": sensor.digital_status
            }

        # except IntegrityError as e:
        #     # Handle duplicate key error (unique constraint violation)
        #     self.conn.rollback()  # Rollback transaction on error
        #     error_message = f"Duplicate entry for PlantID: {plant.PlantID}. A plant with this ID already exists."
        #     print(f"IntegrityError: {e}")
        #     return {
        #         "status": "error",
        #         "error": error_message
        #     }

        except (psycopg2.Error, DatabaseError) as db_error:
            # Handle other database errors
            self.conn.rollback()  # Rollback transaction on error
            error_message = f"Database error: {db_error}"
            print(f"Database error: {db_error}")
            return {
                "status": "error",
                "error": error_message
            }

        except ValueError as val_error:
            # Handle input validation errors
            error_message = f"Invalid input: {val_error}"
            print(f"Input error: {val_error}")
            return {
                "status": "error",
                "error": error_message
            }

        except Exception as e:
            # Catch any other unexpected errors
            self.conn.rollback()  # Rollback transaction on error
            error_message = f"Unexpected error: {e}"
            print(f"Unexpected error: {e}")
            return {
                "status": "error",
                "error": error_message
            }

        finally:
            # Ensure that the connection is released
            release_connection(self.conn)