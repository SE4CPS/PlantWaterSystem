#!/bin/bash
# PlantWaterSystem setup script

echo "Starting PlantWaterSystem setup..."

# Get active user and home directory.
ACTIVE_USER=$(whoami)
ACTIVE_HOME=$HOME

echo "Active user: $ACTIVE_USER"
echo "Home directory: $ACTIVE_HOME"

# Step 1: Clone the repository if not already present.
if [ ! -d "PlantWaterSystem" ]; then
    echo "Cloning the PlantWaterSystem repository..."
    git clone https://github.com/SE4CPS/PlantWaterSystem.git
fi

cd PlantWaterSystem/embedded || exit

# Step 2: Update Raspberry Pi OS.
echo "Updating Raspberry Pi OS..."
sudo apt update && sudo apt upgrade -y

# Step 3: Enable I2C communication.
echo "Enabling I2C communication..."
CONFIG_FILE="/boot/config.txt"
I2C_LINE="dtparam=i2c_arm=on"
REBOOT_REQUIRED=false
if ! grep -q "$I2C_LINE" "$CONFIG_FILE"; then
    echo "I2C not enabled. Adding configuration..."
    sudo bash -c "echo '$I2C_LINE' >> $CONFIG_FILE"
    REBOOT_REQUIRED=true
else
    echo "I2C is already enabled."
fi

# Step 4: Install I2C tools and python3-smbus.
echo "Installing I2C tools..."
sudo apt install -y i2c-tools python3-smbus

# Step 5: Install required packages.
echo "Installing required packages..."
sudo apt install -y python3-pip sqlite3

echo "Installing necessary Python libraries..."
sudo pip3 install RPi.GPIO adafruit-circuitpython-ads1x15 requests flask schedule --break-system-packages

# Step 6: Verify I2C connection.
echo "Verifying I2C connection..."
i2cdetect -y 1
if i2cdetect -y 1 | grep -q "48"; then
    echo "I2C device detected at address 0x48."
else
    echo "Warning: No I2C device detected. Please check connections."
fi

# Step 7: Set executable permission for plant_monitor.py.
if [ -f "plant_monitor.py" ]; then
    echo "Setting executable permission for plant_monitor.py..."
    chmod +x plant_monitor.py
else
    echo "Warning: plant_monitor.py not found!"
fi

# Step 8: Setup systemd service for plant_monitor.
SERVICE_FILE="/etc/systemd/system/plant_monitor.service"
cat <<EOF | sudo tee $SERVICE_FILE
[Unit]
Description=Plant Moisture Monitoring Service
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 $ACTIVE_HOME/PlantWaterSystem/embedded/plant_monitor.py
WorkingDirectory=$ACTIVE_HOME/PlantWaterSystem/embedded
StandardOutput=inherit
StandardError=inherit
Restart=always
RestartSec=5
TimeoutStopSec=10
User=$ACTIVE_USER

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
sudo systemctl enable plant_monitor.service
sudo systemctl start plant_monitor.service

# Step 9: Optional: Setup systemd service for send_data_api.
SEND_API_SERVICE_FILE="/etc/systemd/system/send_data_api.service"
read -p "Do you want to set up send_data_api.py as a service? (y/n): " SETUP_SEND_API
if [[ "$SETUP_SEND_API" == "y" || "$SETUP_SEND_API" == "Y" ]]; then
    echo "Setting up send_data_api service..."
    cat <<EOF | sudo tee $SEND_API_SERVICE_FILE
[Unit]
Description=Send Data API Service
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 $ACTIVE_HOME/PlantWaterSystem/embedded/send_data_api.py
WorkingDirectory=$ACTIVE_HOME/PlantWaterSystem/embedded
StandardOutput=inherit
StandardError=inherit
Restart=always
RestartSec=5
TimeoutStopSec=10
User=$ACTIVE_USER

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable send_data_api.service
    sudo systemctl start send_data_api.service
else
    echo "Skipping send_data_api service setup."
fi

# Step 10: Reboot if necessary.
if [ "$REBOOT_REQUIRED" = true ]; then
    echo "I2C configuration updated. Reboot is required."
    read -p "Reboot now? (y/n): " REBOOT_ANSWER
    if [[ "$REBOOT_ANSWER" == "y" || "$REBOOT_ANSWER" == "Y" ]]; then
        echo "Rebooting..."
        sudo reboot
    else
        echo "Please reboot later to apply changes."
    fi
else
    echo "No reboot required."
fi

echo "Setup complete. Check services with:"
echo "sudo systemctl status plant_monitor.service"
echo "sudo systemctl status send_data_api.service (if configured)"
