from langgraph.graph import StateGraph, START, END

from graph.state import WeatherState
from tools.geocoding import geocode_location
from tools.weather import get_weather
from llm.gemini import llm


# ============================================================
# 1. GEOCODING NODE
# ============================================================

def geocoding_node(state: WeatherState) -> dict:
    """
    Convert the user's location into latitude and longitude.
    """

    location = state["location"]

    result = geocode_location.invoke(location)

    return {
        "latitude": result["latitude"],
        "longitude": result["longitude"],
        "location_name": result["name"],
        "country": result["country"],
        "state": result["state"],
    }


# ============================================================
# 2. WEATHER NODE
# ============================================================

def weather_node(state: WeatherState) -> dict:
    """
    Fetch current, hourly, and daily weather data.
    """

    latitude = state["latitude"]
    longitude = state["longitude"]

    weather = get_weather.invoke({
        "latitude": latitude,
        "longitude": longitude,
    })

    return {
        "current_weather": weather["current"],
        "hourly_forecast": weather["hourly"],
        "daily_forecast": weather["daily"],
        "timezone": weather["timezone"],
    }


# ============================================================
# 3. GEMINI NODE
# ============================================================

def gemini_node(state: WeatherState) -> dict:
    """
    Generate a human-readable weather report from
    the factual current and hourly weather data.

    The 5-day forecast is NOT included in the Gemini report.
    It will be displayed separately in the Streamlit UI.
    """

    location_name = state["location_name"]
    state_name = state.get("state", "")
    country = state.get("country", "")

    current = state["current_weather"]
    hourly = state["hourly_forecast"]

    # --------------------------------------------------------
    # Today's hourly forecast
    # --------------------------------------------------------

    today_hourly = hourly[:24]

    # --------------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------------

    prompt = f"""
You are a weather assistant.

Generate a clear and useful weather report for the user.

IMPORTANT RULES:

1. Use ONLY the weather data provided below.
2. Do not invent weather values.
3. Do not estimate missing values.
4. Do not change any numerical weather values.
5. Do not provide a 5-day forecast.
6. The 5-day forecast will be displayed separately
   by the application.

Location:
{location_name}, {state_name}, {country}

CURRENT WEATHER:
{current}

TODAY'S HOURLY FORECAST:
{today_hourly}


Create the report using exactly these sections:


1. Current Weather

- Explain the current temperature.
- Mention the feels-like temperature.
- Mention humidity.
- Mention the current weather condition.
- Mention wind speed and wind gusts.
- Mention pressure.
- Mention current precipitation and rain.


2. Today's Weather

- Explain how the weather is expected to develop
  throughout the day.
- Mention important temperature changes.
- Mention periods with high rain probability.
- Mention thunderstorms if present.
- Mention when rain probability decreases.
- Mention notable changes between morning,
  afternoon, evening, and night.


3. Rain Analysis

- Explain today's rain probability.
- Identify periods when rain is most likely.
- Mention whether rain appears persistent,
  intermittent, or concentrated in certain hours.
- Do not confuse rain probability with rainfall amount.
- Mention thunderstorms if they occur.


4. Practical Advice

- Give simple practical advice based strictly on
  the provided weather data.
- Mention an umbrella or rain protection when
  rain probability is high.
- Mention strong wind precautions when wind or
  wind gusts are significant.
- Do not give medical advice.


Keep the report concise but informative.

Use °C and km/h.

Do not create a 5-day outlook.

Do not make up sunrise or sunset information.

Do not mention information that is not present
in the provided weather data.
"""

    # --------------------------------------------------------
    # Call Gemini
    # --------------------------------------------------------

    response = llm.invoke(prompt)

    # --------------------------------------------------------
    # Extract Gemini response
    # --------------------------------------------------------

    if isinstance(response.content, str):

        response_text = response.content

    else:

        response_text = ""

        for block in response.content:

            if isinstance(block, dict):

                if block.get("type") == "text":
                    response_text += block.get("text", "")

            else:

                response_text += str(block)

    # --------------------------------------------------------
    # Return response
    # --------------------------------------------------------

    return {
        "response": response_text
    }


# ============================================================
# 4. BUILD LANGGRAPH
# ============================================================

builder = StateGraph(WeatherState)


# ------------------------------------------------------------
# Add nodes
# ------------------------------------------------------------

builder.add_node(
    "geocoding",
    geocoding_node
)

builder.add_node(
    "weather",
    weather_node
)

builder.add_node(
    "gemini",
    gemini_node
)


# ------------------------------------------------------------
# Define workflow
# ------------------------------------------------------------

builder.add_edge(
    START,
    "geocoding"
)

builder.add_edge(
    "geocoding",
    "weather"
)

builder.add_edge(
    "weather",
    "gemini"
)

builder.add_edge(
    "gemini",
    END
)


# ============================================================
# 5. COMPILE GRAPH
# ============================================================

weather_graph = builder.compile()