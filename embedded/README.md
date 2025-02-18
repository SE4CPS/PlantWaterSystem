# Setting Up PlantWaterSystem on a New Raspberry Pi

This guide will walk you through setting up a new Raspberry Pi for your Soil Moisture Monitoring System using:
- Raspberry Pi
- Capacitive Soil Moisture Sensor
- ADS1115 Analog-to-Digital Converter (ADC)
- SQLite Database
- Python (for data processing and logging)

---

## **1. Hardware Requirements**
### **Components Needed**
1. Raspberry Pi (any model with GPIO support)
2. Capacitive Soil Moisture Sensor
3. ADS1115 ADC Module
4. Jumper Wires
5. Power Supply for Raspberry Pi

---

## **2. Wiring Connections**

### **ADS1115 (ADC) to Raspberry Pi**
| ADS1115 Pin | Raspberry Pi GPIO Pin |
|-------------|------------------------|
| VDD         | 3.3V (Pin 1)           |
| GND         | GND (Pin 9)            |
| SCL         | GPIO3 (SCL, Pin 5)      |
| SDA         | GPIO2 (SDA, Pin 3)      |
| ADDR        | GPIO7 (Pin 7)           |
| ALRT        | GPIO0 (Pin 11)          |

### **Capacitive Soil Moisture Sensor to ADS1115**
| Sensor Pin | ADS1115 Pin |
|------------|-------------|
| VCC        | 5V (Pin 2)  |
| GND        | GND (Pin 14)|
| Sensor 1 AO| A0          |
| Sensor 2 AO| A1          |
| Sensor 3 AO| A2          |
| Sensor 4 AO| A3          |

### **Capacitive Soil Moisture Sensor Digital Output to Raspberry Pi**
| Sensor DO Pin | Raspberry Pi GPIO      |
|---------------|-------------------------|
| Sensor 1 AO   | GPIO8 (Pin 8)           |
| Sensor 2 AO   | GPIO15 (Pin 10)         |
| Sensor 3 AO   | GPIO18 (Pin 12)         |
| Sensor 4 AO   | GPIO23 (Pin 16)         |

---

## **3. Setup Options**

### **Automated Setup**
Run the following command to clone the repository, install dependencies, and configure the system automatically:

```bash
bash <(curl -L https://raw.githubusercontent.com/SE4CPS/PlantWaterSystem/embedded-code/Embedded/setup.sh)
```

This command performs the following tasks:
- Clones the PlantWaterSystem repository.
- Updates your Raspberry Pi OS.
- Installs required packages and Python libraries.
- Verifies I2C connection.
- Configures auto-start for the `plant_monitor.py` script using `systemd`.

Check the service status after setup:

```bash
sudo systemctl status plant_monitor.service
```

If you choose to set up the `send_data_api.py` service, check its status with:

```bash
sudo systemctl status send_data_api.service
```

---

### **Manual Setup (or for Debugging)**

If you prefer a manual setup or need to debug, follow these steps:

### **Step 1: Clone the Repository**
```bash
git clone git@github.com:SE4CPS/PlantWaterSystem.git
cd PlantWaterSystem/Embedded
```

### **Step 2: Update Raspberry Pi OS**
```bash
sudo apt update && sudo apt upgrade -y
```

### **Step 3: Enable I2C Communication**

Check if I2C is enabled:
```bash
ls /dev/i2c-*
```

If you don’t see a response, enable I2C:
```bash
sudo raspi-config
```
Navigate to **Interfacing Options** → **I2C** → Enable.

### **Step 4: Install Required Packages**
```bash
sudo apt install -y python3-pip python3-smbus i2c-tools sqlite3
sudo pip3 install RPi.GPIO adafruit-circuitpython-ads1x15 --break-system-packages
```

### **Step 5: Verify I2C Devices**
```bash
i2cdetect -y 1
```
Ensure the address `0x48` appears to confirm the connection.

### **Step 6: Set Permissions and Run the Script**
```bash
chmod +x plant_monitor.py
python3 plant_monitor.py
```

The output should display something like:
```
Starting Plant Sensor Monitoring...
Raw ADC Value: 18345, Moisture Level: 54.23%, Digital Status: Dry
```

### **Step 7: Set Up Auto-Start (Optional)**

#### **Option 1: Using systemd (Recommended)**

1. Create a service file for `plant_monitor.py`:
   ```bash
   sudo nano /etc/systemd/system/plant_monitor.service
   ```

2. Paste the following:
   ```ini
   [Unit]
   Description=Plant Moisture Monitoring Service
   After=multi-user.target

   [Service]
   ExecStart=/usr/bin/python3 /home/pi/PlantWaterSystem/Embedded/plant_monitor.py
   WorkingDirectory=/home/pi/PlantWaterSystem/Embedded
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable plant_monitor.service
   sudo systemctl start plant_monitor.service
   ```

4. Check the service status:
   ```bash
   sudo systemctl status plant_monitor.service
   ```

#### **Option 2: Set Up Auto-Start for `send_data_api.py`**

If you want to run `send_data_api.py` automatically, follow these steps:

1. Create a service file for `send_data_api.py`:
   ```bash
   sudo nano /etc/systemd/system/send_data_api.service
   ```

2. Paste the following:
   ```ini
   [Unit]
   Description=Send Data API Service
   After=multi-user.target

   [Service]
   ExecStart=/usr/bin/python3 /home/pi/PlantWaterSystem/Embedded/send_data_api.py
   WorkingDirectory=/home/pi/PlantWaterSystem/Embedded
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable send_data_api.service
   sudo systemctl start send_data_api.service
   ```

4. Check the service status:
   ```bash
   sudo systemctl status send_data_api.service
   ```

---

## **4. Testing & Debugging**

### **To View Logs:**
```bash
journalctl -u plant_monitor.service --follow
```
For `send_data_api.py`:
```bash
journalctl -u send_data_api.service --follow
```

### **To Restart the Service:**
```bash
sudo systemctl restart plant_monitor.service
```
For `send_data_api.py`:
```bash
sudo systemctl restart send_data_api.service
```

### **To Manually View Data:**
```bash
sqlite3 plant_sensor_data.db "SELECT * FROM moisture_data;"
