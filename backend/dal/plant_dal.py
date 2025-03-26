from config.database import get_connection, release_connection
from schemas.plant_schema import PlantSchema
import psycopg2 
from psycopg2 import  DatabaseError, IntegrityError
from pathlib import Path
import os
from fastapi.responses import FileResponse



class PlantDAL:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def create_plant(self, plant: PlantSchema):
        try:
            # Validate input data (optional, based on your requirements)
            if not plant.PlantName or not plant.ScientificName or not isinstance(plant.Threshold, (int, float)):
                raise ValueError("Invalid input data")

            # Execute the query to insert the plant data
            self.cursor.execute("""
                INSERT INTO plant (PlantID, PlantName, ScientificName, Threshold, ImageFileName)
                VALUES (%s, %s, %s, %s, %s) RETURNING PlantID;
            """, (plant.PlantID, plant.PlantName, plant.ScientificName, plant.Threshold, plant.ImageFilename))

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
                "Threshhold": plant.Threshhold,
                "ImageFilename": plant.ImageFilename
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

    def get_plants(self):
        try:
           
            self.cursor.execute( "SELECT PlantID, PlantName, ScientificName, Threshold FROM plant;") # + ImageFilename maybe?

            plants= self.cursor.fetchall()

            if not plants:
                return {
                    "status": "success",
                    "message": "No plants found",
                    "data": []
                }
            
            plant_list=[
            {
                "PlantID": plant[0],
                "PlantName": plant[1],
                "ScientificName": plant[2],
                "Threshhold": plant[3]
                #"ImageFilename" plant[4]
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


    def update_plant_image(self, plant_id: int, new_image_filename: str, file_content: bytes):
        try:
            # Query for the current image filename
            self.cursor.execute("SELECT ImageFilename FROM plant WHERE PlantID = %s;", (plant_id,))
            result = self.cursor.fetchone()
            if not result:
                return {"status": "error", "error": "Plant not found"}

            current_image_filename = result[0]

            # Define the image directory
            IMAGE_DIR = Path("/path/to/your/image/directory")

            # Delete the old image file if it exists
            if current_image_filename:
                old_image_path = IMAGE_DIR / current_image_filename
                if old_image_path.exists():
                    os.remove(old_image_path)

            # Save the new image file
            new_image_path = IMAGE_DIR / new_image_filename
            with open(new_image_path, "wb") as buffer:
                buffer.write(file_content)

            # Update the image filename in the database
            self.cursor.execute("""
                UPDATE plant
                SET ImageFilename = %s
                WHERE PlantID = %s;
            """, (new_image_filename, plant_id))

            # Commit the transaction
            self.conn.commit()

            # Return the updated image
            return FileResponse(
            path=str(new_image_path),            
            filename=new_image_filename
        )


        except (psycopg2.Error, DatabaseError) as db_error:
            # Handle database errors
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