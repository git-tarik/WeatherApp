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
# SESSION STATE
# ============================================================

if "weather_result" not in st.session_state:
    st.session_state.weather_result = None


if "shown_sections" not in st.session_state:
    st.session_state.shown_sections = []


# ============================================================
# HEADER
# ============================================================

st.title("🌤️ Weather Assistant")

st.write(
    "Enter a city, town, or village to get current weather "
    "and an AI-generated weather report."
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
# GET WEATHER
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

                # Save result in session
                st.session_state.weather_result = result

                # Reset opened sections for new search
                st.session_state.shown_sections = []

            except Exception as e:

                st.error(
                    f"Unable to fetch weather: {str(e)}"
                )

                st.stop()


# ============================================================
# DISPLAY WEATHER
# ============================================================

if st.session_state.weather_result:

    result = st.session_state.weather_result


    # ========================================================
    # LOCATION
    # ========================================================

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


    # ========================================================
    # CURRENT WEATHER
    # ========================================================

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


    # ========================================================
    # GEMINI REPORT
    # ========================================================

    st.subheader("🤖 AI Weather Report")

    st.markdown(
        result["response"]
    )


    st.divider()


    # ========================================================
    # AVAILABLE SECTIONS
    # ========================================================

    sections = [
        (
            "hourly",
            "🕐 Today's Hourly Forecast"
        ),
        (
            "daily",
            "📅 5-Day Forecast"
        ),
        (
            "sun",
            "🌅 Today's Sunrise & Sunset"
        ),
    ]


    # ========================================================
    # DISPLAY ALREADY SELECTED SECTIONS
    # ========================================================

    for section in st.session_state.shown_sections:


        # ====================================================
        # HOURLY FORECAST
        # ====================================================

        if section == "hourly":

            st.subheader(
                "🕐 Today's Hourly Forecast"
            )

            hourly = result["hourly_forecast"]

            hourly_table = []

            for hour in hourly[:24]:

                hourly_table.append({

                    "Time": hour["time"],

                    "Temperature": (
                        f"{hour['temperature']} °C"
                    ),

                    "Feels Like": (
                        f"{hour['feels_like']} °C"
                    ),

                    "Rain Probability": (
                        f"{hour['rain_probability']}%"
                    ),

                    "Condition": hour["condition"],

                    "Humidity": (
                        f"{hour['humidity']}%"
                    ),

                    "Wind": (
                        f"{hour['wind_speed']} km/h"
                    ),

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

        elif section == "daily":

            st.subheader(
                "📅 5-Day Forecast"
            )

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
        # SUNRISE / SUNSET
        # ====================================================

        elif section == "sun":

            st.subheader(
                "🌅 Today's Sunrise & Sunset"
            )

            daily = result["daily_forecast"]

            # First daily entry = today
            today = daily[0]

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "🌅 Sunrise",
                    today["sunrise"]
                )

            with col2:

                st.metric(
                    "🌇 Sunset",
                    today["sunset"]
                )


    # ========================================================
    # REMAINING BUTTONS
    # ========================================================

    remaining_sections = [
        section
        for section in sections
        if section[0]
        not in st.session_state.shown_sections
    ]


    if remaining_sections:

        st.subheader("More Weather Details")


        columns = st.columns(
            len(remaining_sections)
        )


        for column, (section_id, label) in zip(
            columns,
            remaining_sections
        ):

            with column:

                if st.button(
                    label,
                    key=f"button_{section_id}",
                    use_container_width=True
                ):

                    st.session_state.shown_sections.append(
                        section_id
                    )

                    st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Weather data provided by Open-Meteo. "
    "AI analysis generated using Gemini."
)