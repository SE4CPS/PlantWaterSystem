# Central configuration and device serial extraction

# Time intervals (in seconds)
SENSOR_READ_INTERVAL = 900         # 15 minutes between sensor readings
DATA_RETENTION_DAYS = 7            # Days to retain data in the database
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

# Function to extract the device's unique serial number from /proc/cpuinfo
def get_device_serial():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith("Serial"):
                    return line.split(":")[1].strip()
    except Exception as e:
        return "0000000000000000"

DEVICE_ID = get_device_serial()
