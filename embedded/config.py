# Central configuration for the Plant Moisture Monitoring System

# Intervals (in seconds)
SENSOR_READ_INTERVAL = 900         # 15 minutes between sensor readings
DATA_RETENTION_DAYS = 30            # Days to retain data in the database
WEATHER_FETCH_INTERVAL = 900       # 15 minutes between weather API calls

# ADC conversion settings
MIN_ADC = 5000                   # ADC value corresponding to 100% moisture
MAX_ADC = 20000                  # ADC value corresponding to 0% moisture

# CSV output settings
ENABLE_CSV_OUTPUT = True
CSV_FILENAME = "plant_data_temp.csv"

# Database settings
DB_NAME = "plant_sensor_data.db"

# Backend API settings (for send_data_api)
BACKEND_API_URL = "https://sprout-ly.com/api/sensor/data"
RETRY_ATTEMPTS = 3
BASE_DELAY = 2
