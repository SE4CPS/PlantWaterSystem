from config.database import get_connection, release_connection
from schemas.user_schema import UserSchema
import psycopg2 
from psycopg2 import DatabaseError

class UserDAL:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def get_user(self, email: str):
        try:
            if not email:
                raise ValueError("email must not be empty.")

            self.cursor.execute("""
                SELECT sensorid, firstname, lastname, username, userpassword, email 
                FROM userdata
                WHERE email = %s
            """, (email,))

            user = self.cursor.fetchone()

            if user is None:
                return None

            return {
                "sensorid": user[0],
                "firstname": user[1],
                "lastname": user[2],
                "username": user[3],
                "userpassword": user[4],
                "email": user[5]
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
        
    def create_user(self, sensorid: int, firstname: str, lastname: str, username: str, userpassword: str, email: str):
        try:
            if not username:
                raise ValueError("Username must not be empty.")
            if not userpassword:
                raise ValueError("Password must not be empty.")
            if not firstname:
                raise ValueError("First name must not be empty.")
            if not lastname:
                raise ValueError("Last name must not be empty.")
            if not email:
                raise ValueError("Email must not be empty.")

            self.cursor.execute("""
                INSERT INTO userdata (sensorid, firstname, lastname, username, userpassword, email) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                RETURNING sensorid, firstname, lastname, username, userpassword, email
            """, (sensorid, firstname, lastname, username, userpassword, email))

            user = self.cursor.fetchone()

            if user is None:
                return None

            self.conn.commit()

            return {
                "sensorid": user[0],
                "firstname": user[1],
                "lastname": user[2],
                "username": user[3],
                "userpassword": user[4],
                "email": user[5]
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
        

    def __del__(self):
        """ Ensure the connection is closed when the object is destroyed. """
        if self.conn:
            release_connection(self.conn)