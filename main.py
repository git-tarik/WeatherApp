from graph.workflow import weather_graph


def print_current_weather(result):
    """
    Print current weather information.
    """

    current = result["current_weather"]

    print("\n")
    print("=" * 70)
    print("CURRENT WEATHER")
    print("=" * 70)

    print(f"Temperature      : {current['temperature']} °C")
    print(f"Feels Like       : {current['feels_like']} °C")
    print(f"Condition        : {current['condition']}")
    print(f"Humidity         : {current['humidity']} %")
    print(f"Rain             : {current['rain']} mm")
    print(f"Precipitation    : {current['precipitation']} mm")
    print(f"Wind Speed       : {current['wind_speed']} km/h")
    print(f"Wind Direction   : {current['wind_direction']}°")
    print(f"Wind Gusts       : {current['wind_gusts']} km/h")
    print(f"Pressure         : {current['pressure']} hPa")
    print(f"Cloud Cover      : {current['cloud_cover']} %")


def print_hourly_forecast(result):
    """
    Print today's hourly forecast.
    """

    hourly = result["hourly_forecast"]

    print("\n")
    print("=" * 70)
    print("TODAY'S HOURLY FORECAST")
    print("=" * 70)

    print(
        f"{'Time':<20}"
        f"{'Temp':<10}"
        f"{'Feels':<10}"
        f"{'Rain %':<10}"
        f"{'Condition'}"
    )

    print("-" * 70)

    # First 24 hours = today's forecast
    for hour in hourly[:24]:

        time = hour["time"]
        temperature = hour["temperature"]
        feels_like = hour["feels_like"]
        rain_probability = hour["rain_probability"]
        condition = hour["condition"]

        print(
            f"{time:<20}"
            f"{str(temperature) + ' °C':<10}"
            f"{str(feels_like) + ' °C':<10}"
            f"{str(rain_probability) + ' %':<10}"
            f"{condition}"
        )


def print_daily_forecast(result):
    """
    Print 5-day forecast.
    """

    daily = result["daily_forecast"]

    print("\n")
    print("=" * 70)
    print("5-DAY FORECAST")
    print("=" * 70)

    print(
        f"{'Date':<15}"
        f"{'High':<12}"
        f"{'Low':<12}"
        f"{'Rain %':<12}"
        f"{'Condition'}"
    )

    print("-" * 70)

    for day in daily:

        date = day["date"]
        high = day["high_temperature"]
        low = day["low_temperature"]
        rain_probability = day["rain_probability"]
        condition = day["condition"]

        print(
            f"{date:<15}"
            f"{str(high) + ' °C':<12}"
            f"{str(low) + ' °C':<12}"
            f"{str(rain_probability) + ' %':<12}"
            f"{condition}"
        )


def print_sun_times(result):
    """
    Print sunrise and sunset for the forecast days.
    """

    daily = result["daily_forecast"]

    print("\n")
    print("=" * 70)
    print("SUNRISE & SUNSET")
    print("=" * 70)

    for day in daily:

        print(
            f"{day['date']} | "
            f"Sunrise: {day['sunrise']} | "
            f"Sunset: {day['sunset']}"
        )


def print_gemini_report(result):
    """
    Print Gemini's human-readable analysis.
    """

    print("\n")
    print("=" * 70)
    print("GEMINI WEATHER ANALYSIS")
    print("=" * 70)

    print(result["response"])


def main():

    print("=" * 70)
    print("WEATHER ASSISTANT")
    print("=" * 70)

    location = input(
        "\nEnter city/town/village name: "
    ).strip()

    if not location:

        print("Please enter a location.")

        return

    print(
        f"\nFetching weather information for {location}..."
    )

    try:

        result = weather_graph.invoke({
            "location": location
        })

        # --------------------------------------------------
        # LOCATION
        # --------------------------------------------------

        print("\n")
        print("=" * 70)
        print("LOCATION")
        print("=" * 70)

        print(
            f"{result['location_name']}, "
            f"{result['state']}, "
            f"{result['country']}"
        )

        print(
            f"Coordinates: "
            f"{result['latitude']}, "
            f"{result['longitude']}"
        )

        print(
            f"Timezone: {result['timezone']}"
        )

        # --------------------------------------------------
        # CURRENT WEATHER
        # --------------------------------------------------

        print_current_weather(result)

        # --------------------------------------------------
        # HOURLY FORECAST
        # --------------------------------------------------

        print_hourly_forecast(result)

        # --------------------------------------------------
        # DAILY FORECAST
        # --------------------------------------------------

        print_daily_forecast(result)

        # --------------------------------------------------
        # SUNRISE / SUNSET
        # --------------------------------------------------

        print_sun_times(result)

        # --------------------------------------------------
        # GEMINI
        # --------------------------------------------------

        print_gemini_report(result)

        print("\n")
        print("=" * 70)
        print("END OF WEATHER REPORT")
        print("=" * 70)

    except Exception as e:

        print("\n")
        print("=" * 70)
        print("ERROR")
        print("=" * 70)

        print(str(e))


if __name__ == "__main__":
    main()