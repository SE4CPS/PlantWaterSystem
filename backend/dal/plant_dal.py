from config.database import get_connection, release_connection
from schemas.plant_schema import PlantSchema
import psycopg2 
from psycopg2 import  DatabaseError, IntegrityError

class PlantDAL:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def create_plant(self, plant: PlantSchema, username: str):
        try:
            # Validate input data
            if not plant.plant_name or not isinstance(plant.device_id, str) or not isinstance(plant.sensor_id, str):
                raise ValueError("Invalid input data")

            # Get the user's ID
            self.cursor.execute("""
                SELECT userid FROM UserData WHERE UserName = %s
            """, (username,))
            user_result = self.cursor.fetchone()
            if not user_result:
                raise ValueError(f"User with username {username} not found")
            user_id = user_result[0]

            # Execute the query to insert the plant data with UserId
            self.cursor.execute("""
                WITH new_plant AS (
                    INSERT INTO Plant (plantname, userid)
                    VALUES (%s, %s)
                    RETURNING plantid
                )
                UPDATE Sensors 
                SET plantid = new_plant.plantid
                FROM new_plant
                WHERE deviceid = %s AND sensorid = %s;
            """, (plant.plant_name, user_id, plant.device_id, plant.sensor_id))

            self.conn.commit()

            # Return the response including required fields
            return {
                "status": "success",
                "plant_name": plant.plant_name,
                "user_id": user_id,
                "sensor_id": plant.sensor_id,
                "device_id": plant.device_id,
                "message": "Plant created and sensors updated."
            }

        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "error": str(e)}

    def get_plants(self, username: str):
        try:
           
            self.cursor.execute("SELECT FirstName, LastName, PlantName, ScientificName FROM UserData JOIN Plant ON UserData.UserId = Plant.UserId WHERE username = %s;", (username,))

            plants= self.cursor.fetchall()

            if not plants:
                return {
                    "status": "success",
                    "message": "No plants found",
                    "data": []
                }
            
            plant_list=[
            {
                "FirstName": plant[0],
                "LastName": plant[1],
                "PlantName": plant[2],
                "ScientificName": plant[3]
            }
                for plant in plants
            ]

            return {
                "status": "success",
                "data": plant_list
            }

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

    def delete_plant(self, sensor_id: str, username: str):
        try:
            self.cursor.execute("""
                WITH de_plant AS (
                    SELECT plantid
                    FROM Sensors 
                    WHERE sensorid = %s
                ),
                update_sensor AS (
                    UPDATE Sensors
                    SET plantid = NULL
                    WHERE sensorid = %s
                )
                DELETE FROM Plant
                WHERE plantid IN (SELECT plantid FROM de_plant);
            """, (sensor_id, sensor_id))
            self.conn.commit()
            return {"status": "success", "message": "Plant deleted successfully."}
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "error": str(e)}
        finally:
            release_connection(self.conn)   