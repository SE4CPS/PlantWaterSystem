from connection import DatabaseConnection

class PlantQueries:
    
    def create_table(self):
        """Creates the Plant table if it does not exist."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS Plant (
                        PlantID SERIAL PRIMARY KEY,
                        PlantName VARCHAR(50) NOT NULL,
                        ScientificName VARCHAR(50) NOT NULL,
                        Threshhold FLOAT(3) NOT NULL
                    );
                """)
                conn.commit()
        finally:
            DatabaseConnection.release_connection(conn)

    def insert_plant(self, plant_name, scientific_name, threshold):
        """Inserts a new plant record."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO Plant (PlantName, ScientificName, Threshhold) VALUES (%s, %s, %s) RETURNING PlantID;", 
                            (plant_name, scientific_name, threshold))
                plant_id = cur.fetchone()[0]
                conn.commit()
                return plant_id
        finally:
            DatabaseConnection.release_connection(conn)

    def get_plants(self):
        """Fetches all plant records."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM Plant;")
                return cur.fetchall()
        finally:
            DatabaseConnection.release_connection(conn)

    def update_plant(self, plant_id, plant_name, scientific_name, threshold):
        """Updates a plant record by ID."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE Plant SET PlantName = %s, ScientificName = %s, Threshhold = %s WHERE PlantID = %s RETURNING PlantID;", 
                            (plant_name, scientific_name, threshold, plant_id))
                updated_id = cur.fetchone()
                conn.commit()
                return updated_id is not None
        finally:
            DatabaseConnection.release_connection(conn)

    def delete_plant(self, plant_id):
        """Deletes a plant record by ID."""
        conn = DatabaseConnection.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM Plant WHERE PlantID = %s RETURNING PlantID;", (plant_id,))
                deleted_id = cur.fetchone()
                conn.commit()
                return deleted_id is not None
        finally:
            DatabaseConnection.release_connection(conn)
