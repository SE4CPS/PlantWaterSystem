#!/bin/bash


print_message() {
    echo -e "\033[1;34m-------------------------------------\033[0m"
    echo -e "\033[1;36m$1\033[0m"
    echo -e "\033[1;34m-------------------------------------\033[0m"
}


print_welcome() {
    echo -e "\033[1;32m"
    echo "**********************************************"
    echo "       WELCOME TO THE SPROUTLY SETUP!        "
    echo "**********************************************"
    echo -e "\033[1;33m Let's get your environment set up for success! \033[0m"
    echo -e "\033[1;32m"
    echo "**********************************************"
    echo -e "\033[0m"
}

# Step 1: Print the welcome message
print_welcome

# Step 2: Navigate to the backend folder
print_message "Navigating to the backend folder..."
cd "$(dirname "$0")" || exit 1

# Step 3: Ensure Docker is installed
print_message "Checking if Docker is installed..."
if command -v docker &> /dev/null; then
    echo -e "\033[1;32mDocker is already installed! Let's keep moving.\033[0m"
else
    print_message "Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Step 4: Ensure Docker Compose is installed
print_message "Checking if Docker Compose is installed..."
if command -v docker-compose &> /dev/null; then
    echo -e "\033[1;32mDocker Compose is good to go!\033[0m"
else
    print_message "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Step 5: Navigate to the docker directory where docker-compose.yml is located
print_message "Setting up the Docker environment..."
DOCKER_DIR="./docker"

# Step 6: Build and start the Docker containers
print_message "Starting Docker containers with Docker Compose..."
docker-compose -f "$DOCKER_DIR/docker-compose.yml" down
docker-compose -f "$DOCKER_DIR/docker-compose.yml" up -d --build

# Step 7: Verify containers are running
print_message "Checking if the containers are up and running..."
docker ps

# Step 8: Add sproutly.com to /etc/hosts for local testing
print_message "Updating your /etc/hosts for local testing..."
if ! grep -q "sproutly.com" /etc/hosts; then
    echo "127.0.0.1 sproutly.com" | sudo tee -a /etc/hosts
    echo -e "\033[1;32mAdded sproutly.com to /etc/hosts. Now you can test locally!\033[0m"
else
    echo -e "\033[1;33msproutly.com is already in /etc/hosts.\033[0m"
fi

# Step 9: Show Docker containers status at the end
print_message "🎉 Setup Complete! 🎉"
echo -e "\033[1;32mThe following Docker containers are now running:\033[0m"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Final completion message with a bit more flair
echo -e "\033[1;34mThank you for setting up Sproutly with us! 🌱 Your environment is now ready.\033[0m"
echo -e "\033[1;32mYou can start testing at: http://sproutly.com/api/plant/data\033[0m"
