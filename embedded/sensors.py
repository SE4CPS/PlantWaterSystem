#!/usr/bin/env python3

import board
import busio
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import logging
from config import MIN_ADC, MAX_ADC

def init_ads():
    """Initializes the I2C bus and returns an ADS1115 instance."""
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    return ads

def convert_adc_to_moisture(adc_value):
    """Converts a raw ADC value to a moisture percentage using MIN_ADC and MAX_ADC."""
    moisture_level = ((MAX_ADC - adc_value) / (MAX_ADC - MIN_ADC)) * 100
    return max(0, min(100, moisture_level))

def read_sensor_channel(ads, sensor_config):
    """
    Reads the ADC channel and digital input for a given sensor.
    Returns a tuple: (adc_value, moisture_level, digital_status)
    """
    try:
        chan = AnalogIn(ads, sensor_config["analog"])
        adc_value = chan.value
        if adc_value == 0 or adc_value > 32767:
            logging.warning(f"Sensor channel {sensor_config['analog']} might be disconnected.")
            return adc_value, 0, "Disconnected"
        moisture_level = convert_adc_to_moisture(adc_value)
        digital_status = "Dry" if GPIO.input(sensor_config["digital"]) == GPIO.HIGH else "Wet"
        return adc_value, moisture_level, digital_status
    except Exception as e:
        logging.error(f"Error reading sensor {sensor_config['analog']}: {e}")
        return 0, 0, "Error"
