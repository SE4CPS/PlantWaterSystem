import os

DB_URI = "postgresql://neondb_owner:npg_u3CHa6zJfBcy@ep-round-frog-a5ts8fvg-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

class Config:
    SQLALCHEMY_DATABASE_URI = DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
