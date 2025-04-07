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
                INSERT INTO sensorsdata (
                    readingid, timestamp, deviceid, sensorid, adcvalue, moisturelevel, digitalstatus,
                    weathertemp, weatherhumidity, weathersunlight, weatherwindspeed, location, weatherfetched
                ) VALUES %s RETURNING readingid;
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

    def get_sensor_data(self, username: str):
        try:
           
            self.cursor.execute("""
                SELECT FirstName, LastName, PlantName, ScientificName, Sensors.SensorId, Sensors.DeviceId
                FROM UserData
                JOIN Plant ON UserData.UserId = Plant.UserId
                JOIN Sensors ON Plant.PlantId = Sensors.PlantId
                WHERE UserName = %s;
            """, (username,))

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
                    "readingid": row[0],           # readingid
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

    def update_sensor_data(self, reading_id: str, update_data: dict):
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
                    "error": f"No sensor data found with ID: {reading_id}"
                }

            # Build the update query dynamically based on provided fields
            update_fields = []
            values = []
            for key, value in update_data.items():
                if key in ['timestamp', 'sensorid', 'adcvalue', 'moisturelevel', 'digitalstatus',
                          'weathertemp', 'weatherhumidity', 'weathersunlight', 'weatherwindspeed',
                          'location', 'weatherfetched']:
                    update_fields.append(f"{key} = %s")
                    values.append(value)

            if not update_fields:
                return {
                    "status": "error",
                    "error": "No valid fields to update"
                }

            # Add reading_id to values for the WHERE clause
            values.append(reading_id)

            # Construct and execute the update query
            update_query = f"""
                UPDATE sensorsdata 
                SET {', '.join(update_fields)}
                WHERE readingid = %s
                RETURNING readingid;
            """
            
            self.cursor.execute(update_query, values)
            self.conn.commit()

            updated_id = self.cursor.fetchone()
            if updated_id:
                return {
                    "status": "success",
                    "message": f"Successfully updated sensor data with ID: {reading_id}"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Failed to update sensor data with ID: {reading_id}"
                }

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

    def add_sensor_data(self, sensor_data: dict):
        try:
            # Insert query with all required fields
            insert_query = """
                INSERT INTO sensorsdata (
                    readingid, sensorid, deviceid, adcvalue, moisturelevel, digitalstatus,
                    weathertemp, weatherhumidity, weathersunlight, weatherwindspeed,
                    weatherfetched, timestamp, location
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING readingid, timestamp, sensorid, adcvalue, moisturelevel, digitalstatus,
                         weathertemp, weatherhumidity, weathersunlight, weatherwindspeed,
                         location, weatherfetched;
            """
            
            # Prepare values for insertion
            values = (
                sensor_data['readingid'],
                sensor_data['sensorid'],
                sensor_data['deviceid'],
                sensor_data['adcvalue'],
                sensor_data['moisturelevel'],
                sensor_data['digitalstatus'],
                sensor_data['weathertemp'],
                sensor_data['weatherhumidity'],
                sensor_data['weathersunlight'],
                sensor_data['weatherwindspeed'],
                sensor_data['weatherfetched'],
                sensor_data['timestamp'],
                sensor_data['location']
            )
            
            # Execute the insert query
            self.cursor.execute(insert_query, values)
            self.conn.commit()
            
            # Get the inserted data
            row = self.cursor.fetchone()
            
            # Convert datetime objects to strings
            timestamp_str = str(row[1]) if row[1] else None
            weather_fetched_str = str(row[11]) if row[11] else None
            
            # Format the response with all fields
            inserted_data = {
                "reading": row[0],           # readingid
                "timestamp": timestamp_str,     # timestamp
                "sensor_id": row[2],    
                "adc_value": row[3],     # adcvalue
                "moisture_level": row[4],# moisturelevel
                "digital_status": row[5],# digitalstatus
                "weather_temp": row[6],  # weathertemp
                "weather_humidity": row[7],  # weatherhumidity
                "weather_sunlight": row[8],  # weathersunlight
                "weather_wind_speed": row[9],  # weatherwindspeed
                "location": row[10],     # location
                "weather_fetched": weather_fetched_str  # weatherfetched
            }
            
            return {
                "status": "success",
                "message": "Sensor data added successfully",
                "data": inserted_data
            }

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

    def get_sensor_data_by_username(self, username: str):   
        try:
            if not username:
                raise ValueError("Username must not be empty.")

            self.cursor.execute("""
                SELECT firstname, lastname, plantname, threshold, Sensors.sensorid, Sensors.deviceid
                FROM UserData
                JOIN Plant ON UserData.UserId = Plant.UserId
                JOIN Sensors ON Plant.PlantId = Sensors.PlantId
                WHERE UserName = %s
            """, (username,))

            results = self.cursor.fetchall()

            if not results:
                return []

            return [
                {
                    "firstname": row[0],
                    "lastname": row[1],
                    "plantname": row[2],
                    "threshold": row[3],
                    "sensorid": row[4],
                    "deviceid": row[5]
                }
                for row in results
            ]

        except (psycopg2.Error, DatabaseError) as db_error:
            self.conn.rollback()
            print(f"Database error: {db_error}")
            return {"status": "error", "error": str(db_error)}

        except ValueError as val_error:
            print(f"Input error: {val_error}")
            return {"status": "error", "error": str(val_error)}

        except Exception as e:
            self.conn.rollback()
            print(f"Unexpected error: {e}")
            return {"status": "error", "error": str(e)}

    def get_sensor_data_details_by_sensorid_and_deviceid(self, sensorid: str, deviceid: str):
        try:

            self.cursor.execute("""
                SELECT readingid, adcvalue, moisturelevel AS "Water Level", digitalstatus, timestamp AS "Date_Time"
                FROM sensorsdata
                WHERE sensorid = %s AND deviceid = %s 
                ORDER BY readingid DESC 
                LIMIT 5
            """, (sensorid, deviceid))

            results = self.cursor.fetchall()

            if not results:
                return []

            return [
                {
                    "id": row[0],  # readingid
                    "adcvalue": row[1],
                    "waterlevel": row[2],
                    "digitalsatus": row[3],
                    "moisture_level": row[2],  # Using moisturelevel as moisture_level
                    "date": row[4].date() if row[4] else None,  # Extract date from timestamp
                    "time": row[4].time() if row[4] else None   # Extract time from timestamp
                }
                for row in results
            ]
        except (psycopg2.Error, DatabaseError) as db_error:
            self.conn.rollback()
            print(f"Database error: {db_error}")
            return {"status": "error", "error": str(db_error)}

        except ValueError as val_error:
            print(f"Input error: {val_error}")
            return {"status": "error", "error": str(val_error)}

        except Exception as e:
            self.conn.rollback()
            print(f"Unexpected error: {e}")
            return {"status": "error", "error": str(e)}

    def get_last_status(self, sensorid: str, deviceid: str):
        try:
            self.cursor.execute("""
                SELECT digitalstatus
                FROM sensorsdata
                WHERE sensorid = %s AND deviceid = %s
                ORDER BY readingid DESC
                LIMIT 1
                """, (sensorid, deviceid))
            
            results = self.cursor.fetchone()

            if not results:
                return {"digital_status": "Unknown"}
                
            return {
                "digital_status": results[0]
            }

        except (psycopg2.Error, DatabaseError) as db_error:
            self.conn.rollback()
            print(f"Database error: {db_error}")
            return {"status": "error", "error": str(db_error)}

        except ValueError as val_error:
            print(f"Input error: {val_error}")          
            return {"status": "error", "error": str(val_error)}

        except Exception as e:
            self.conn.rollback()
            print(f"Unexpected error: {e}")
            return {"status": "error", "error": str(e)} 
        
    def get_sensor_id_by_device_id(self, deviceid: str):
        try:
            self.cursor.execute("""
                SELECT sensorid
                FROM sensors
                WHERE deviceid = %s
            """, (deviceid,))
            
            results = self.cursor.fetchall()
            print(results)
            if not results:
                return {"sensorid": []}
            return {
                "sensor_ids": [row[0] for row in results]
            }
            
        except (psycopg2.Error, DatabaseError) as db_error:
            self.conn.rollback()
            print(f"Database error: {db_error}")
            return {"status": "error", "error": str(db_error)}

        except Exception as e:
            self.conn.rollback()
            print(f"Unexpected error: {e}")
            return {"status": "error", "error": str(e)} 