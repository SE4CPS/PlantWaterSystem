from config.database import get_connection, release_connection
from schemas.user_schema import UserSchema
import psycopg2 
from psycopg2 import DatabaseError

class UserDAL:
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def verify_user(self, user: UserSchema):
        try:
            if not user.username or not user.password:
                raise ValueError("Username and password must not be empty.")

            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM users WHERE username = %s AND password = %s
                );
            """, (user.username, user.password))

            return self.cursor.fetchone()[0]  # Returns True or False

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
