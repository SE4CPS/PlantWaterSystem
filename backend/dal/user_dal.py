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
                raise ValueError("username must not be empty.")

            self.cursor.execute("""
                SELECT userid, firstname, lastname, username, email, phonenumber, userpassword, deviceid
                FROM userdata
                WHERE username = %s
            """, (username,))

            user = self.cursor.fetchone()

            if user is None:
                return None

            return {
                "userid": user[0],
                "firstname": user[1],
                "lastname": user[2],
                "username": user[3],
                "email": user[4],
                "phonenumber": user[5],
                "userpassword": user[6],
                "deviceid": user[7]
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
        
    def create_user(self, firstname: str, lastname: str, username: str, userpassword: str, email: str, phonenumber: str):
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
            if not phonenumber:
                raise ValueError("Phone must not be empty.")

            self.cursor.execute("""
                INSERT INTO userdata (firstname, lastname, username, userpassword, email, phonenumber) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                RETURNING userid, firstname, lastname, username, userpassword, email, phonenumber
            """, (firstname, lastname, username, userpassword, email, phonenumber))

            user = self.cursor.fetchone()

            if user is None:
                return None

            self.conn.commit()

            return {
                "userid": user[0],
                "firstname": user[1],
                "lastname": user[2],
                "username": user[3],
                "userpassword": user[4],
                "email": user[5],
                "phonenumber": user[6]
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