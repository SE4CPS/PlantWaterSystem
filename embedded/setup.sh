#!/bin/bash

echo "Starting PlantWaterSystem setup..."

# Step 1: Clone the repository (only if not already cloned)
if [ ! -d "PlantWaterSystem" ]; then
    echo "Cloning the PlantWaterSystem repository..."
    git clone -b embedded-code https://github.com/SE4CPS/PlantWaterSystem.git
fi

# Navigate to the directory
cd PlantWaterSystem/embedded || exit

# Step 2: Update Raspberry Pi OS
echo "Updating Raspberry Pi OS..."
sudo apt update && sudo apt upgrade -y

# Step 3: Enable I2C Communication Automatically
echo "Enabling I2C communication..."
CONFIG_FILE="/boot/config.txt"
I2C_LINE="dtparam=i2c_arm=on"
REBOOT_REQUIRED=false

# Check if I2C is already enabled
if ! grep -q "$I2C_LINE" "$CONFIG_FILE"; then
    echo "I2C not enabled. Adding the configuration to $CONFIG_FILE..."
    sudo bash -c "echo '$I2C_LINE' >> $CONFIG_FILE"
    REBOOT_REQUIRED=true
else
    echo "I2C is already enabled."
fi

# Install I2C tools (if not installed)
echo "Installing I2C tools..."
sudo apt install -y i2c-tools python3-smbus

# Step 4: Install Required Packages
echo "Installing required packages..."
sudo apt install -y python3-pip sqlite3

echo "Installing necessary Python libraries..."
sudo pip3 install RPi.GPIO adafruit-circuitpython-ads1x15 --break-system-packages

# Step 5: Verify I2C Devices
echo "Verifying I2C connection..."
i2cdetect -y 1
if i2cdetect -y 1 | grep -q "48"; then
    echo "I2C device detected successfully at address 0x48."
else
    echo "Warning: No I2C device detected. Please check your connections."
fi

# Step 6: Set Permissions and Run Python Script
cd PlantWaterSystem/embedded || exit

if [ -f "plant_monitor.py" ]; then
    echo "Setting executable permission for the plant_monitor.py script..."
    chmod +x plant_monitor.py
else
    echo "Warning: plant_monitor.py not found!"
fi

# Step 7: Setup Auto-Start with systemd
echo "Setting up auto-start using systemd..."
SERVICE_FILE="/etc/systemd/system/plant_monitor.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Plant Moisture Monitoring Service
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/PlantWaterSystem/embedded/plant_monitor.py
WorkingDirectory=/home/pi/PlantWaterSystem/embedded
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling and starting the plant_monitor service..."
sudo systemctl enable plant_monitor.service
sudo systemctl start plant_monitor.service

# Step 8: Reboot if required
if [ "$REBOOT_REQUIRED" = true ]; then
    echo "The system needs to reboot to apply I2C configuration changes."
    read -p "Do you want to reboot now? (y/n): " REBOOT_ANSWER
    if [[ "$REBOOT_ANSWER" == "y" || "$REBOOT_ANSWER" == "Y" ]]; then
        echo "Rebooting now..."
        sudo reboot
    else
        echo "Please remember to reboot later to apply I2C configuration changes."
    fi
else
    echo "No reboot required."
fi

echo "Setup is complete. You can now check the service status with:"
echo "sudo systemctl status plant_monitor.service"

echo "If you want to manually run the script, use:"
echo "python3 plant_monitor.py"
