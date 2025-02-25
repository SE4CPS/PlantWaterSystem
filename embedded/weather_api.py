#!/usr/bin/env python3
import os
import requests
import logging

# Fallback coordinates from environment (optional)
FALLBACK_LAT = os.getenv("FALLBACK_LAT", "")
FALLBACK_LON = os.getenv("FALLBACK_LON", "")

def get_ipinfo_location():
    """
    Try to get location using ipinfo.io.
    Returns (latitude, longitude) or (None, None) on failure.
    """
    try:
        response = requests.get("https://ipinfo.io/json", timeout=10)
        response.raise_for_status()
        data = response.json()
        loc_str = data.get("loc", None)  # e.g., "40.7128,-74.0060"
        if loc_str:
            lat_str, lon_str = loc_str.split(",")
            return float(lat_str), float(lon_str)
    except Exception as e:
        logging.error(f"Failed to get location from ipinfo.io: {e}")
    return None, None

def get_geoplugin_location():
    """
    Try to get location using geoplugin.net.
    Returns (latitude, longitude) or (None, None) on failure.
    """
    try:
        response = requests.get("http://www.geoplugin.net/json.gp", timeout=10)
        response.raise_for_status()
        data = response.json()
        lat_str = data.get("geoplugin_latitude", None)
        lon_str = data.get("geoplugin_longitude", None)
        if lat_str and lon_str:
            return float(lat_str), float(lon_str)
    except Exception as e:
        logging.error(f"Failed to get location from geoplugin.net: {e}")
    return None, None

def detect_location():
    """
    Attempt multiple IP-based geolocation methods.
    If they fail, use fallback coordinates from the environment.
    Returns (latitude, longitude) or (None, None) if all methods fail.
    """
    # Try ipinfo.io
    lat, lon = get_ipinfo_location()
    if lat is not None and lon is not None:
        logging.info(f"Got location from ipinfo.io: {lat}, {lon}")
        return lat, lon

    # Try geoplugin.net
    lat, lon = get_geoplugin_location()
    if lat is not None and lon is not None:
        logging.info(f"Got location from geoplugin.net: {lat}, {lon}")
        return lat, lon

    # Fallback: use environment variables if available
    if FALLBACK_LAT and FALLBACK_LON:
        try:
            lat = float(FALLBACK_LAT)
            lon = float(FALLBACK_LON)
            logging.info(f"Using fallback coordinates from environment: {lat}, {lon}")
            return lat, lon
        except ValueError:
            logging.error("Invalid fallback coordinates; check FALLBACK_LAT and FALLBACK_LON.")

    logging.warning("All location methods failed. Returning (None, None).")
    return None, None

def get_weather_data(lat, lon):
    """
    Fetch current weather data from Open-Meteo for the given lat/lon.
    Returns a tuple:
      (weather_temp, weather_humidity, weather_sunlight, weather_wind_speed)
    where:
      - weather_temp: current temperature (°C)
      - weather_humidity: current relative humidity (%)
      - weather_sunlight: current shortwave radiation (W/m², proxy for sunlight)
      - weather_wind_speed: current wind speed (m/s)
    If retrieval fails, returns (None, None, None, None).

    This call uses the "current_weather" feature along with hourly parameters
    "relativehumidity_2m" and "shortwave_radiation" to align with the current time.
    """
    if lat is None or lon is None:
        logging.warning("Latitude/Longitude not available. Cannot fetch weather data.")
        return None, None, None, None
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "hourly": "relativehumidity_2m,shortwave_radiation",
            "timezone": "auto"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current_weather", {})
        weather_temp = current.get("temperature")
        weather_wind_speed = current.get("windspeed")
        current_time = current.get("time")

        # Default humidity and sunlight to None
        weather_humidity = None
        weather_sunlight = None

        hourly = data.get("hourly", {})
        hourly_time = hourly.get("time", [])
        hourly_humidity = hourly.get("relativehumidity_2m", [])
        hourly_radiation = hourly.get("shortwave_radiation", [])

        if current_time and hourly_time:
            try:
                index = hourly_time.index(current_time)
                if index < len(hourly_humidity):
                    weather_humidity = hourly_humidity[index]
                if index < len(hourly_radiation):
                    weather_sunlight = hourly_radiation[index]
            except ValueError:
                # current_time not found; use first available values
                if hourly_humidity:
                    weather_humidity = hourly_humidity[0]
                if hourly_radiation:
                    weather_sunlight = hourly_radiation[0]
        else:
            if hourly_humidity:
                weather_humidity = hourly_humidity[0]
            if hourly_radiation:
                weather_sunlight = hourly_radiation[0]

        return weather_temp, weather_humidity, weather_sunlight, weather_wind_speed
    except Exception as e:
        logging.error(f"Failed to retrieve weather data from Open-Meteo: {e}")
        return None, None, None, None
