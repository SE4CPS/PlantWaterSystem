from config.database import get_connection, release_connection
from schemas.user_schema import UserSchema
import psycopg2 
from psycopg2 import DatabaseError

class UserDAL:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def get_user(self, username: str):
        try:
            if not username:
                raise ValueError("Username must not be empty.")

            self.cursor.execute("""
                SELECT username, password FROM users WHERE username = %s
            """, (username,))

            user = self.cursor.fetchone()

            if user is None:
                return None

            return {
                "username": user[0],
                "password": user[1],
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
