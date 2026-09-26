from typing import TypedDict


class WeatherState(TypedDict, total=False):

    # User input
    location: str

    # Geocoding
    latitude: float
    longitude: float
    location_name: str
    country: str
    state: str

    # Weather
    current_weather: dict
    hourly_forecast: list
    daily_forecast: list
    timezone: str

    # Gemini response
    response: str