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
    the factual weather data.
    """

    location_name = state["location_name"]
    state_name = state.get("state", "")
    country = state.get("country", "")

    current = state["current_weather"]
    hourly = state["hourly_forecast"]
    daily = state["daily_forecast"]

    # We only send today's 24 hours to Gemini
    # for the hourly analysis.
    today_hourly = hourly[:24]

    prompt = f"""
You are a weather assistant.

Generate a clear and useful weather report for the user.

IMPORTANT RULE:
Use ONLY the weather data provided below.
Do not invent, estimate, or change any weather values.

Location:
{location_name}, {state_name}, {country}

CURRENT WEATHER:
{current}

TODAY'S HOURLY FORECAST:
{today_hourly}

5-DAY FORECAST:
{daily}

Create the report using this structure:

1. Current Weather
- Explain the current temperature.
- Mention feels-like temperature.
- Mention humidity.
- Mention current weather condition.
- Mention wind.
- Mention pressure.
- Mention current precipitation/rain.

2. Today's Weather
- Explain how the weather is expected to develop
  throughout the day.
- Mention important changes in temperature.
- Mention periods with high rain probability.
- Mention thunderstorms if present.
- Mention when rain probability decreases.

3. Rain Analysis
- Explain today's rain probability.
- Mention whether rain is likely to be persistent,
  intermittent, or limited to certain hours.
- Do not confuse rain probability with rainfall amount.

4. 5-Day Outlook
- Summarize the temperature trend.
- Mention high and low temperatures.
- Mention rain probability.
- Mention notable weather changes.

5. Practical Advice
- Give simple practical advice based strictly on
  the provided weather.
- For example, mention an umbrella if rain probability
  is high.
- Do not give medical advice.

Keep the report concise but informative.
Use °C and km/h.

Do not make up sunrise or sunset information.
"""

    response = llm.invoke(prompt)

    # Gemini/LangChain can return content either as a
    # normal string or as a list of content blocks.

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

    return {
        "response": response_text
    }


# ============================================================
# 4. BUILD LANGGRAPH
# ============================================================

builder = StateGraph(WeatherState)


# Add nodes
builder.add_node("geocoding", geocoding_node)
builder.add_node("weather", weather_node)
builder.add_node("gemini", gemini_node)


# Define workflow
builder.add_edge(START, "geocoding")
builder.add_edge("geocoding", "weather")
builder.add_edge("weather", "gemini")
builder.add_edge("gemini", END)


# ============================================================
# 5. COMPILE GRAPH
# ============================================================

weather_graph = builder.compile()