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

    def get_sensor_data(self):
        try:
           
            self.cursor.execute("SELECT readingid, timestamp, sensorid, adcvalue, moisturelevel, digitalstatus, weathertemp, weatherhumidity, weathersunlight, weatherwindspeed, location, weatherfetched FROM sensorsdata;")

            data= self.cursor.fetchall()

            if not data:
                return []

            all_sensor_data = [
                {
                    "id": row[0],           # readingid
                    "timestamp": row[1],     # timestamp
                    "sensor_id": row[2],    
                    "adc_value": row[3],     # adcvalue
                    "moisture_level": row[4],# moisturelevel
                    "digital_status": row[5],# digitalstatus
                    "weather_temp": row[6],  # weathertemp
                    "weather_humidity": row[7],  # weatherhumidity
                    "weather_sunlight": row[8],  # weathersunlight
                    "weather_wind_speed": row[9],  # weatherwindspeed
                    "location": row[10],     # location
                    "weather_fetched": row[11]  # weatherfetched
                }
                for row in data
            ]

            return all_sensor_data

        except (psycopg2.Error, DatabaseError) as db_error:
            # Handle other database errors
            self.conn.rollback()  # Rollback transaction on error
            error_message = f"Database error: {db_error}"
            print(f"Database error: {db_error}")
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

    def get_sensor_data_by_id(self, sensor_id: str):
        try:
            self.cursor.execute("""
                SELECT readingid, timestamp, sensorid, adcvalue, moisturelevel, digitalstatus, 
                       weathertemp, weatherhumidity, weathersunlight, weatherwindspeed, location, weatherfetched 
                FROM sensorsdata 
                WHERE sensorid = %s;
            """, (sensor_id,))

            data = self.cursor.fetchall()

            if not data:
                return {
                    "status": "error",
                    "error": f"No sensor data found with ID: {sensor_id}"
                }

            sensor_data = [
                {
                    "id": row[0],           # readingid
                    "timestamp": row[1],     # timestamp
                    "sensor_id": row[2],    
                    "adc_value": row[3],     # adcvalue
                    "moisture_level": row[4],# moisturelevel
                    "digital_status": row[5],# digitalstatus
                    "weather_temp": row[6],  # weathertemp
                    "weather_humidity": row[7],  # weatherhumidity
                    "weather_sunlight": row[8],  # weathersunlight
                    "weather_wind_speed": row[9],  # weatherwindspeed
                    "location": row[10],     # location
                    "weather_fetched": row[11]  # weatherfetched
                }
                for row in data
            ]

            return sensor_data

        except (psycopg2.Error, DatabaseError) as db_error:
            self.conn.rollback()
            error_message = f"Database error: {db_error}"
            print(f"Database error: {db_error}")
            return {
                "status": "error",
                "error": error_message
            }

        except Exception as e:
            self.conn.rollback()
            error_message = f"Unexpected error: {e}"
            print(f"Unexpected error: {e}")
            return {
                "status": "error",
                "error": error_message
            }

        finally:
            release_connection(self.conn)

    def delete_sensor_data(self, reading_id: str):
        try:
            # Check if the reading_id exists
            self.cursor.execute(
                "SELECT readingid FROM sensorsdata WHERE readingid = %s;",
                (reading_id,)
            )
            existing_record = self.cursor.fetchone()

            if not existing_record:
                return {
                    "status": "error",
                    "message": f"No sensor data found with ID: {reading_id}"
                }

            # Delete the record
            self.cursor.execute(
                "DELETE FROM sensorsdata WHERE readingid = %s;",
                (reading_id,)
            )
            self.conn.commit()  # Commit the transaction

            return {
                "status": "success",
                "message": f"Successfully deleted sensor data with ID: {reading_id}"
            }

        except (psycopg2.Error, DatabaseError) as db_error:
            self.conn.rollback()  # Rollback on error
            error_message = f"Database error: {db_error}"
            print(f"Database error: {db_error}")
            return {
                "status": "error",
                "error": error_message
            }

        except Exception as e:
            self.conn.rollback()  # Rollback on error
            error_message = f"Unexpected error: {e}"
            print(f"Unexpected error: {e}")
            return {
                "status": "error",
                "error": error_message
            }

        finally:
            release_connection(self.conn)  # Release the connection