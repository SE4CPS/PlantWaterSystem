# Use official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

RUN ls

# Copy the dependencies file
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose port (change as per your app)
EXPOSE 5000

# Command to run the app
CMD ["python", "app.py"]
