from psycopg2 import pool
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql://neondb_owner:npg_SbW8PXa4dpzK@ep-summer-poetry-a84hp8dp-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
connection_pool = pool.SimpleConnectionPool(1, 10, DATABASE_URL)
engine = create_engine(DATABASE_URL)
Base = declarative_base()

def get_connection():
    print("hey i'm here ----")
    return connection_pool.getconn()

def release_connection(conn):
    connection_pool.putconn(conn)
