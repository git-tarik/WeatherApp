import requests
from langchain_core.tools import tool


@tool
def geocode_location(location: str) -> dict:
    """
    Convert a city, town, or village name into latitude and longitude.
    """

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": location,
        "count": 5,
        "language": "en",
        "format": "json"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception("Geocoding API request failed.")

    data = response.json()

    if "results" not in data or not data["results"]:
        raise ValueError(f"Location '{location}' was not found.")

    result = data["results"][0]

    return {
        "name": result.get("name"),
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "country": result.get("country"),
        "state": result.get("admin1")
    }