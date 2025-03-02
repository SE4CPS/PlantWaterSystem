# Dockerfile for PlantWaterSystem
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 5001 (for Flask API)
EXPOSE 5001

# Run plant_monitor.py as the main process
CMD ["python", "plant_monitor.py"]
