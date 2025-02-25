#!/usr/bin/env python3

import os
import requests
import logging

# Fallback coordinates from environment (optional)
FALLBACK_LAT = os.getenv("FALLBACK_LAT", "")
FALLBACK_LON = os.getenv("FALLBACK_LON", "")

# Queries ipinfo.io for geolocation; returns (lat, lon, location_name).
def get_ipinfo_location():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=10)
        response.raise_for_status()
        data = response.json()
        loc_str = data.get("loc", None)
        if loc_str:
            lat_str, lon_str = loc_str.split(",")
            lat = float(lat_str)
            lon = float(lon_str)
            city = data.get("city", "")
            region = data.get("region", "")
            country = data.get("country", "")
            location_name = ", ".join(filter(None, [city, region, country]))
            if not location_name:
                location_name = f"{lat},{lon}"
            return lat, lon, location_name
    except Exception as e:
        logging.error(f"Failed to get location from ipinfo.io: {e}")
    return None, None, None

# Queries geoplugin.net for geolocation; returns (lat, lon, location_name).
def get_geoplugin_location():
    try:
        response = requests.get("http://www.geoplugin.net/json.gp", timeout=10)
        response.raise_for_status()
        data = response.json()
        lat_str = data.get("geoplugin_latitude", None)
        lon_str = data.get("geoplugin_longitude", None)
        if lat_str and lon_str:
            lat = float(lat_str)
            lon = float(lon_str)
            city = data.get("geoplugin_city", "")
            region = data.get("geoplugin_region", "")
            country = data.get("geoplugin_countryName", "")
            location_name = ", ".join(filter(None, [city, region, country]))
            if not location_name:
                location_name = f"{lat},{lon}"
            return lat, lon, location_name
    except Exception as e:
        logging.error(f"Failed to get location from geoplugin.net: {e}")
    return None, None, None

# Attempts multiple geolocation services and returns (lat, lon, location_name); falls back if needed.
def detect_location():
    lat, lon, loc_name = get_ipinfo_location()
    if lat is not None and lon is not None:
        logging.info(f"Location from ipinfo.io: {lat}, {lon}, {loc_name}")
        return lat, lon, loc_name
    lat, lon, loc_name = get_geoplugin_location()
    if lat is not None and lon is not None:
        logging.info(f"Location from geoplugin.net: {lat}, {lon}, {loc_name}")
        return lat, lon, loc_name
    if FALLBACK_LAT and FALLBACK_LON:
        try:
            lat = float(FALLBACK_LAT)
            lon = float(FALLBACK_LON)
            loc_name = f"{lat},{lon}"
            logging.info(f"Using fallback coordinates: {lat}, {lon}")
            return lat, lon, loc_name
        except ValueError:
            logging.error("Invalid fallback coordinates; check FALLBACK_LAT and FALLBACK_LON.")
    logging.warning("All location methods failed. Returning (None, None, 'Unknown').")
    return None, None, "Unknown"

# Fetches current weather data from Open-Meteo for the provided lat/lon.
def get_weather_data(lat, lon):
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
        logging.error(f"Failed to retrieve weather data: {e}")
        return None, None, None, None
