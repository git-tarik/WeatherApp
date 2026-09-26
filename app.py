import streamlit as st

from graph.workflow import weather_graph


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Weather Assistant",
    page_icon="🌤️",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("🌤️ Weather Assistant")

st.write(
    "Enter a city, town, or village to get current weather, "
    "hourly forecast, 5-day forecast, and an AI-generated report."
)


# ============================================================
# LOCATION INPUT
# ============================================================

location = st.text_input(
    "Enter location",
    placeholder="e.g. Ranchi, Kolkata, Delhi"
)


search_button = st.button(
    "Get Weather",
    type="primary"
)


# ============================================================
# WEATHER REQUEST
# ============================================================

if search_button:

    if not location.strip():

        st.warning("Please enter a city or location.")

    else:

        with st.spinner(
            f"Fetching weather for {location}..."
        ):

            try:

                result = weather_graph.invoke({
                    "location": location.strip()
                })

            except Exception as e:

                st.error(
                    f"Unable to fetch weather: {str(e)}"
                )

                st.stop()


        # ====================================================
        # LOCATION
        # ====================================================

        st.success(
            f"Weather found for "
            f"{result['location_name']}, "
            f"{result['state']}, "
            f"{result['country']}"
        )

        st.caption(
            f"Timezone: {result['timezone']} | "
            f"Coordinates: "
            f"{result['latitude']}, "
            f"{result['longitude']}"
        )


        # ====================================================
        # CURRENT WEATHER
        # ====================================================

        st.subheader("🌡️ Current Weather")

        current = result["current_weather"]

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Temperature",
                f"{current['temperature']} °C"
            )

        with col2:

            st.metric(
                "Feels Like",
                f"{current['feels_like']} °C"
            )

        with col3:

            st.metric(
                "Humidity",
                f"{current['humidity']}%"
            )

        with col4:

            st.metric(
                "Condition",
                current["condition"]
            )


        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Wind",
                f"{current['wind_speed']} km/h"
            )

        with col2:

            st.metric(
                "Wind Gusts",
                f"{current['wind_gusts']} km/h"
            )

        with col3:

            st.metric(
                "Pressure",
                f"{current['pressure']} hPa"
            )

        with col4:

            st.metric(
                "Cloud Cover",
                f"{current['cloud_cover']}%"
            )


        # ====================================================
        # GEMINI REPORT
        # ====================================================

        st.subheader("🤖 AI Weather Report")

        st.markdown(
            result["response"]
        )


        # ====================================================
        # TODAY'S HOURLY FORECAST
        # ====================================================

        st.subheader("🕐 Today's Hourly Forecast")

        hourly = result["hourly_forecast"]

        hourly_table = []

        for hour in hourly[:24]:

            hourly_table.append({
                "Time": hour["time"],
                "Temperature": f"{hour['temperature']} °C",
                "Feels Like": f"{hour['feels_like']} °C",
                "Rain Probability": (
                    f"{hour['rain_probability']}%"
                ),
                "Condition": hour["condition"],
                "Humidity": f"{hour['humidity']}%",
                "Wind": f"{hour['wind_speed']} km/h",
                "Visibility": (
                    f"{hour['visibility']} m"
                ),
            })


        st.dataframe(
            hourly_table,
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # 5-DAY FORECAST
        # ====================================================

        st.subheader("📅 5-Day Forecast")

        daily = result["daily_forecast"]

        daily_table = []

        for day in daily:

            daily_table.append({
                "Date": day["date"],
                "Condition": day["condition"],
                "High": (
                    f"{day['high_temperature']} °C"
                ),
                "Low": (
                    f"{day['low_temperature']} °C"
                ),
                "Rain Probability": (
                    f"{day['rain_probability']}%"
                ),
                "Precipitation": (
                    f"{day['precipitation']} mm"
                ),
                "Rain": (
                    f"{day['rain']} mm"
                ),
            })


        st.dataframe(
            daily_table,
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # SUNRISE & SUNSET
        # ====================================================

        st.subheader("🌅 Sunrise & Sunset")

        sunrise_table = []

        for day in daily:

            sunrise_table.append({
                "Date": day["date"],
                "Sunrise": day["sunrise"],
                "Sunset": day["sunset"],
            })


        st.dataframe(
            sunrise_table,
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # ADDITIONAL DETAILS
        # ====================================================

        st.subheader("🌧️ Additional Weather Information")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.write(
                f"**Current Rain:** "
                f"{current['rain']} mm"
            )

            st.write(
                f"**Precipitation:** "
                f"{current['precipitation']} mm"
            )

        with col2:

            st.write(
                f"**Wind Direction:** "
                f"{current['wind_direction']}°"
            )

            st.write(
                f"**Cloud Cover:** "
                f"{current['cloud_cover']}%"
            )

        with col3:

            st.write(
                f"**Wind Gusts:** "
                f"{current['wind_gusts']} km/h"
            )

            st.write(
                f"**Pressure:** "
                f"{current['pressure']} hPa"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Weather data provided by Open-Meteo. "
    "AI analysis generated using Gemini."
)