import psycopg2
from psycopg2 import pool
from backend.config import Config  # Ensure you have a config file with database credentials

class DatabaseConnection:
    """Manages a PostgreSQL connection pool with automatic reconnection handling."""
    
    _connection_pool = None

    @classmethod
    def initialize(cls, min_conn=1, max_conn=10):
        """Initializes the connection pool."""
        if cls._connection_pool is None:
            try:
                cls._connection_pool = pool.SimpleConnectionPool(
                    min_conn,
                    max_conn,
                    dsn=Config.SQLALCHEMY_DATABASE_URI  # Use your database URL
                )
                print("✅ Database connection pool created successfully")
            except psycopg2.DatabaseError as e:
                print(f"❌ Error initializing database connection pool: {e}")
                cls._connection_pool = None

    @classmethod
    def get_connection(cls):
        """Fetches a connection from the pool with retry mechanism."""
        if cls._connection_pool is None:
            raise Exception("Database connection pool is not initialized.")
        
        try:
            return cls._connection_pool.getconn()
        except psycopg2.DatabaseError as e:
            print(f"🔴 Connection error: {e}. Retrying...")
            cls.initialize()  # Reinitialize the pool
            return cls._connection_pool.getconn()

    @classmethod
    def release_connection(cls, conn):
        """Releases a connection back to the pool."""
        if cls._connection_pool and conn:
            cls._connection_pool.putconn(conn)

    @classmethod
    def close_all_connections(cls):
        """Closes all connections in the pool."""
        if cls._connection_pool:
            cls._connection_pool.closeall()
            cls._connection_pool = None
            print("🔴 All database connections closed.")
