import requests
from langchain_core.tools import tool


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def weather_code_to_text(code):
    return WEATHER_CODES.get(code, "Unknown")


@tool
def get_weather(latitude: float, longitude: float) -> dict:
    """
    Get current weather, today's hourly forecast,
    and 5-day forecast for a latitude and longitude.
    """

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        # Current weather
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "wind_gusts_10m,"
            "surface_pressure,"
            "cloud_cover"
        ),

        # Hourly weather
        "hourly": (
            "temperature_2m,"
            "apparent_temperature,"
            "relative_humidity_2m,"
            "precipitation_probability,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "visibility"
        ),

        # Daily weather
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "apparent_temperature_max,"
            "apparent_temperature_min,"
            "precipitation_probability_max,"
            "precipitation_sum,"
            "rain_sum,"
            "precipitation_hours,"
            "weather_code,"
            "sunrise,"
            "sunset,"
            "wind_speed_10m_max,"
            "wind_gusts_10m_max"
        ),

        "forecast_days": 5,
        "timezone": "auto",

        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    if response.status_code != 200:
        raise Exception(
            f"Weather API request failed: "
            f"{response.status_code} - {response.text}"
        )

    data = response.json()

    if "error" in data and data["error"]:
        raise Exception(
            data.get("reason", "Unknown Open-Meteo error")
        )

    # --------------------------------------------------
    # CURRENT WEATHER
    # --------------------------------------------------

    current_data = data.get("current", {})

    current = {
        "time": current_data.get("time"),

        "temperature": current_data.get("temperature_2m"),
        "feels_like": current_data.get("apparent_temperature"),

        "humidity": current_data.get("relative_humidity_2m"),

        "precipitation": current_data.get("precipitation"),
        "rain": current_data.get("rain"),

        "weather_code": current_data.get("weather_code"),
        "condition": weather_code_to_text(
            current_data.get("weather_code")
        ),

        "wind_speed": current_data.get("wind_speed_10m"),
        "wind_direction": current_data.get("wind_direction_10m"),
        "wind_gusts": current_data.get("wind_gusts_10m"),

        "pressure": current_data.get("surface_pressure"),

        "cloud_cover": current_data.get("cloud_cover"),
    }

    # --------------------------------------------------
    # HOURLY WEATHER
    # --------------------------------------------------

    hourly_data = data.get("hourly", {})

    hourly_times = hourly_data.get("time", [])

    hourly_forecast = []

    for i, time in enumerate(hourly_times):

        weather_code = hourly_data["weather_code"][i]

        hourly_forecast.append({
            "time": time,

            "temperature": hourly_data["temperature_2m"][i],

            "feels_like": hourly_data["apparent_temperature"][i],

            "humidity": hourly_data["relative_humidity_2m"][i],

            "rain_probability": (
                hourly_data["precipitation_probability"][i]
            ),

            "precipitation": hourly_data["precipitation"][i],

            "rain": hourly_data["rain"][i],

            "weather_code": weather_code,

            "condition": weather_code_to_text(
                weather_code
            ),

            "wind_speed": hourly_data["wind_speed_10m"][i],

            "wind_direction": (
                hourly_data["wind_direction_10m"][i]
            ),

            "visibility": hourly_data["visibility"][i],
        })

    # --------------------------------------------------
    # DAILY WEATHER
    # --------------------------------------------------

    daily_data = data.get("daily", {})

    daily_times = daily_data.get("time", [])

    daily_forecast = []

    for i, date in enumerate(daily_times):

        weather_code = daily_data["weather_code"][i]

        daily_forecast.append({
            "date": date,

            "high_temperature": (
                daily_data["temperature_2m_max"][i]
            ),

            "low_temperature": (
                daily_data["temperature_2m_min"][i]
            ),

            "high_feels_like": (
                daily_data["apparent_temperature_max"][i]
            ),

            "low_feels_like": (
                daily_data["apparent_temperature_min"][i]
            ),

            "rain_probability": (
                daily_data["precipitation_probability_max"][i]
            ),

            "precipitation": (
                daily_data["precipitation_sum"][i]
            ),

            "rain": (
                daily_data["rain_sum"][i]
            ),

            "precipitation_hours": (
                daily_data["precipitation_hours"][i]
            ),

            "weather_code": weather_code,

            "condition": weather_code_to_text(
                weather_code
            ),

            "sunrise": daily_data["sunrise"][i],

            "sunset": daily_data["sunset"][i],

            "max_wind_speed": (
                daily_data["wind_speed_10m_max"][i]
            ),

            "max_wind_gusts": (
                daily_data["wind_gusts_10m_max"][i]
            ),
        })

    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    return {
        "timezone": data.get("timezone"),

        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),

        "current": current,

        "hourly": hourly_forecast,

        "daily": daily_forecast,
    }