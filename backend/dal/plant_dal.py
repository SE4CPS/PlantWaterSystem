from config.database import get_connection, release_connection
from schemas.plant_schema import PlantSchema
import psycopg2 
from psycopg2 import  DatabaseError, IntegrityError

class PlantDAL:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def create_plant(self, plant: PlantSchema):
        try:
            # Validate input data (optional, based on your requirements)
            if not plant.PlantName or not plant.ScientificName or not isinstance(plant.Threshhold, (int, float)):
                raise ValueError("Invalid input data")

            # Execute the query to insert the plant data
            self.cursor.execute("""
                INSERT INTO plant (PlantID, PlantName, ScientificName, Threshhold)
                VALUES (%s, %s, %s, %s) RETURNING PlantID;
            """, (plant.PlantID, plant.PlantName, plant.ScientificName, plant.Threshhold))

            # Commit the transaction
            self.conn.commit()

            # Get the returned PlantID
            plant_id = self.cursor.fetchone()[0]

            # Return the response in JSON format
            return {
                "status": "success",
                "PlantID": plant_id,
                "PlantName": plant.PlantName,
                "ScientificName": plant.ScientificName,
                "Threshhold": plant.Threshhold
            }

        except IntegrityError as e:
            # Handle duplicate key error (unique constraint violation)
            self.conn.rollback()  # Rollback transaction on error
            error_message = f"Duplicate entry for PlantID: {plant.PlantID}. A plant with this ID already exists."
            print(f"IntegrityError: {e}")
            return {
                "status": "error",
                "error": error_message
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