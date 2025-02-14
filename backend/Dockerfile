# Base image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy the entire backend folder into the container
# Adjusting the path to copy from /backend folder
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"]
