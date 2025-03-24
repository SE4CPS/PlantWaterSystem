from config.database import get_connection, release_connection
from schemas.sensor_schema import MoistureDataSchema
import psycopg2 
from psycopg2 import  DatabaseError, IntegrityError
from typing import List


class SensorDAL:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def receive_moisture_data(self, sensors: List[MoistureDataSchema]):
        try:
            # Bulk insert query
            insert_query = """
                INSERT INTO sensors (
                    id, timestamp, device_id, sensor_id, adc_value, moisture_level, digital_status,
                    weather_temp, weather_humidity, weather_sunlight, weather_wind_speed, location, weather_fetched
                ) VALUES %s RETURNING id;
            """
            # Convert list of objects to list of tuples
            values = [
                (
                    sensor.id, sensor.timestamp, sensor.device_id, sensor.sensor_id, sensor.adc_value,
                    sensor.moisture_level, sensor.digital_status, sensor.weather_temp, sensor.weather_humidity,
                    sensor.weather_sunlight, sensor.weather_wind_speed, sensor.location, sensor.weather_fetched
                )
                for sensor in sensors
            ]
            # Execute bulk insert
            psycopg2.extras.execute_values(self.cursor, insert_query, values)
            self.conn.commit()

            # Get the returned sensor_id
            inserted_ids = [row[0] for row in self.cursor.fetchall()]
            return {"status": "success", "inserted_ids": inserted_ids}

        except (psycopg2.Error, DatabaseError) as db_error:
            # Handle other database errors
            self.conn.rollback()  # Rollback transaction on error
            error_message = f"Database error: {db_error}"
            print(f"Database error: {db_error}")
            return {
                "status": "Database error",
                "error": error_message
            }

        except ValueError as val_error:
            # Handle input validation errors
            error_message = f"Invalid input: {val_error}"
            print(f"Input error: {val_error}")
            return {
                "status": "Value error",
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