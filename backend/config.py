import os

DB_URI = "postgresql://username:password@localhost:5432/sensordb"

class Config:
    SQLALCHEMY_DATABASE_URI = DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
