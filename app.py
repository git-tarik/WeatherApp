import streamlit as st
import textwrap
import re

from graph.workflow import weather_graph


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Weather Assistant",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# HELPER FOR CUSTOM HTML
# ============================================================

def render_html(html_str: str):
    cleaned = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        safe_html = "\n".join([line for line in cleaned.splitlines() if line.strip()])
        st.markdown(safe_html, unsafe_allow_html=True)


# ============================================================
# AI REPORT PARSER (Keeps Current Weather, Removes Title Banner)
# ============================================================

def format_markdown_text(text: str) -> str:
    """Converts bold and italic markdown cleanly to HTML."""
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    return text


def clean_title_text(title: str) -> str:
    """Strips markdown symbols (*, #, _) and cleans title text."""
    title = re.sub(r'[\*\#\_]', '', title)
    return title.strip()


def render_full_width_ai_cards(raw_text: str):
    """
    Parses Gemini's response into 100% full-width stacked cards.
    Keeps all actual weather sections (including Current Weather)
    while discarding single-line report title banners.
    """
    theme_palette = [
        {"icon": "🌡️", "accent": "#2563eb", "tag_bg": "#eff6ff", "tag_border": "#bfdbfe", "tag_text": "#1d4ed8"},
        {"icon": "🕒", "accent": "#7c3aed", "tag_bg": "#f5f3ff", "tag_border": "#ddd6fe", "tag_text": "#6d28d9"},
        {"icon": "🌧️", "accent": "#0284c7", "tag_bg": "#f0f9ff", "tag_border": "#bae6fd", "tag_text": "#0369a1"},
        {"icon": "💡", "accent": "#ea580c", "tag_bg": "#fff7ed", "tag_border": "#fed7aa", "tag_text": "#c2410c"},
        {"icon": "✨", "accent": "#db2777", "tag_bg": "#fdf2f8", "tag_border": "#fbcfe8", "tag_text": "#be185d"},
    ]

    # Pre-clean: strip leading "Weather Report: City..." header line from the text entirely
    cleaned_raw_text = re.sub(
        r'^\s*(?:\*{0,2}Weather Report[:\s].*?\n|\*{0,2}Location[:\s].*?\n)', 
        '', 
        raw_text.strip(), 
        flags=re.IGNORECASE
    )

    # Split into sections based on numbered points (e.g. "1. Current Weather", "## 2. ...")
    raw_sections = re.split(r'\n(?=\s*(?:\d+\.|\#{1,3}\s*\d*\.?)\s+)', cleaned_raw_text.strip())

    if len(raw_sections) <= 1:
        raw_sections = [s for s in cleaned_raw_text.split('\n\n') if s.strip()]

    cards_html = ['<div class="fullwidth-cards-container">']
    section_index = 0

    for sec in raw_sections:
        lines = [l.strip() for l in sec.split('\n') if l.strip()]
        if not lines:
            continue

        first_line = lines[0]
        title_raw = clean_title_text(first_line)
        title_lower = title_raw.lower()

        # 1. Skip report title banners if they still slipped through
        if (
            title_lower.startswith("weather report") 
            or title_lower.startswith("location:")
            or title_lower.startswith("weather summary for")
        ):
            continue

        body_lines = lines[1:] if len(lines) > 1 else []

        # 2. DO NOT create a card if there are no body bullet points/insights
        if not body_lines:
            continue

        theme = theme_palette[section_index % len(theme_palette)]
        section_index += 1

        rows_html = ""

        for item in body_lines:
            clean_item = re.sub(r'^[•\-\*\d\.]+\s*', '', item).strip()
            if not clean_item:
                continue

            # Match '**Label:** Content' pattern
            match = re.match(r'^\*\*(.*?)\*\*[:\s-]*(.*)', clean_item)
            if match:
                tag_label = clean_title_text(match.group(1).strip().rstrip(":"))
                content_text = format_markdown_text(match.group(2).strip())
                rows_html += f"""
                <div class="card-row">
                    <div class="row-tag" style="background: {theme['tag_bg']}; border-color: {theme['tag_border']}; color: {theme['tag_text']};">
                        {tag_label}
                    </div>
                    <div class="row-desc">{content_text}</div>
                </div>
                """
            else:
                content_text = format_markdown_text(clean_item)
                rows_html += f"""
                <div class="card-row">
                    <div class="row-bullet" style="color: {theme['accent']};">✦</div>
                    <div class="row-desc">{content_text}</div>
                </div>
                """

        if not rows_html.strip():
            continue

        card = f"""
        <div class="fullwidth-card" style="border-left-color: {theme['accent']};">
            <div class="fullwidth-card-header">
                <span class="header-icon">{theme['icon']}</span>
                <span class="header-title" style="color: {theme['accent']};">{title_raw}</span>
            </div>
            <div class="fullwidth-card-body">
                {rows_html}
            </div>
        </div>
        """
        cards_html.append(card)

    cards_html.append('</div>')
    render_html("".join(cards_html))


# ============================================================
# SESSION STATE
# ============================================================

if "weather_result" not in st.session_state:
    st.session_state.weather_result = None

if "shown_sections" not in st.session_state:
    st.session_state.shown_sections = []


# ============================================================
# WEATHER TYPE HELPER
# ============================================================

def get_weather_type(weather_code):
    if weather_code in [0, 1]:
        return "sunny"
    if weather_code in [2, 3]:
        return "cloudy"
    if weather_code in [45, 48]:
        return "fog"
    if weather_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return "rain"
    if weather_code in [71, 73, 75, 77, 85, 86]:
        return "snow"
    if weather_code in [95, 96, 99]:
        return "storm"
    return "cloudy"


# ============================================================
# GLOBAL CSS
# ============================================================

render_html(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: transparent !important;
    }

    .main .block-container {
        max-width: 1050px;
        padding-top: 2rem;
        padding-bottom: 4rem;
        position: relative;
        z-index: 2;
    }

    /* FULL-PAGE FIXED BACKGROUND */
    #weather-bg-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 0;
        pointer-events: none;
        overflow: hidden;
        transition: background 0.8s ease;
    }

    .bg-sunny { background: radial-gradient(circle at 85% 15%, #fef08a 0%, #bae6fd 45%, #e0f2fe 100%); }
    .bg-cloudy { background: linear-gradient(180deg, #cbd5e1 0%, #e2e8f0 50%, #f1f5f9 100%); }
    .bg-rain { background: linear-gradient(180deg, #94a3b8 0%, #cbd5e1 60%, #e2e8f0 100%); }
    .bg-storm { background: linear-gradient(180deg, #475569 0%, #64748b 60%, #94a3b8 100%); animation: stormBgFlash 6s infinite; }
    .bg-snow { background: linear-gradient(180deg, #cbd5e1 0%, #e2e8f0 50%, #f8fafc 100%); }
    .bg-fog { background: linear-gradient(180deg, #94a3b8 0%, #cbd5e1 60%, #e2e8f0 100%); }
    .bg-default { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #fdf4ff 100%); }

    .bg-sun {
        position: absolute;
        width: 160px;
        height: 160px;
        border-radius: 50%;
        top: 40px;
        right: 8%;
        background: radial-gradient(circle, #fde047 20%, #facc15 80%);
        box-shadow: 0 0 70px #fde047, 0 0 140px rgba(250, 204, 21, 0.6);
        animation: sunPulse 4s ease-in-out infinite;
    }
    .bg-cloud {
        position: absolute;
        width: 320px;
        height: 90px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 100px;
        filter: blur(1px);
        animation: cloudFloat 45s linear infinite;
    }
    .bg-cloud::before, .bg-cloud::after { content: ""; position: absolute; background: inherit; border-radius: 50%; }
    .bg-cloud::before { width: 130px; height: 130px; left: 45px; bottom: 25px; }
    .bg-cloud::after { width: 160px; height: 160px; right: 40px; bottom: 15px; }
    .cloud-pos-1 { top: 8%; left: -350px; animation-duration: 40s; }
    .cloud-pos-2 { top: 22%; left: -350px; opacity: 0.45; animation-duration: 60s; animation-delay: 10s; }

    .bg-rain-drop {
        position: absolute;
        width: 2px;
        height: 45px;
        background: rgba(59, 130, 246, 0.45);
        top: -60px;
        transform: rotate(15deg);
        animation: rainDown 0.9s linear infinite;
    }
    .bg-lightning { position: absolute; top: 80px; left: 50%; font-size: 80px; color: #fef08a; opacity: 0; animation: lightningFlash 5s infinite; }
    .bg-snowflake { position: absolute; top: -40px; color: rgba(255, 255, 255, 0.85); font-size: 26px; animation: snowDown 6s linear infinite; }

    /* HEADER */
    .weather-header { text-align: center; margin-bottom: 2rem; }
    .weather-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0369a1 0%, #4f46e5 50%, #d946ef 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .weather-subtitle { color: #475569; font-size: 1.05rem; font-weight: 600; }

    /* INPUT & SUBMIT */
    div[data-testid="stTextInput"] input {
        border-radius: 16px;
        border: 2px solid rgba(255, 255, 255, 0.9);
        padding: 0.9rem 1.2rem;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        backdrop-filter: blur(10px);
        font-size: 1.05rem;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15);
    }
    div[data-testid="stButton"] > button {
        border-radius: 16px;
        min-height: 48px;
        font-weight: 700;
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
        color: white;
        border: none;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
        transition: transform 0.2s ease;
    }
    div[data-testid="stButton"] > button:hover { transform: translateY(-2px); }

    /* METRIC CARDS */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(16px);
        border: 1.5px solid rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 1.1rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.04);
    }

    /* LOCATION HEADER */
    .location-card {
        padding: 1.2rem 1.6rem;
        border-radius: 22px;
        margin: 1.5rem 0;
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(16px);
        border: 2px solid #a7f3d0;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.08);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }
    .location-title { font-size: 1.35rem; font-weight: 800; color: #065f46; }
    .location-details {
        color: #047857;
        font-size: 0.95rem;
        font-weight: 600;
        background: rgba(255, 255, 255, 0.9);
        padding: 0.4rem 1rem;
        border-radius: 12px;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 800;
        margin-top: 2.2rem;
        margin-bottom: 1.2rem;
        color: #0f172a;
    }

    /* ========================================================
       FULL-WIDTH HORIZONTAL AI CARDS
       ======================================================== */
    .fullwidth-cards-container {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
        width: 100%;
        margin-top: 1rem;
        margin-bottom: 2rem;
    }

    .fullwidth-card {
        width: 100%;
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(16px);
        border-radius: 20px;
        border: 1.5px solid rgba(255, 255, 255, 0.95);
        border-left: 6px solid #2563eb;
        padding: 1.3rem 1.6rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .fullwidth-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.07);
    }

    .fullwidth-card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid rgba(226, 232, 240, 0.8);
    }

    .header-icon {
        font-size: 1.35rem;
    }

    .header-title {
        font-size: 1.2rem;
        font-weight: 800;
    }

    .fullwidth-card-body {
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
    }

    .card-row {
        display: flex;
        align-items: flex-start;
        gap: 12px;
    }

    .row-tag {
        flex-shrink: 0;
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        padding: 0.35rem 0.75rem;
        border-radius: 10px;
        border: 1px solid transparent;
        min-width: 120px;
        text-align: center;
    }

    .row-bullet {
        font-size: 1rem;
        line-height: 1.5;
    }

    .row-desc {
        font-size: 0.95rem;
        color: #334155;
        line-height: 1.55;
        flex-grow: 1;
    }

    .row-desc strong {
        color: #0f172a;
        font-weight: 700;
    }

    /* MOBILE OPTIMIZATIONS */
    @media (max-width: 768px) {
        .weather-title { font-size: 2.2rem; }
        .fullwidth-card { padding: 1.1rem; }
        .card-row { flex-direction: column; gap: 4px; }
        .row-tag { min-width: auto; align-self: flex-start; }
        .location-card { flex-direction: column; align-items: flex-start; }
    }

    /* KEYFRAMES */
    @keyframes sunPulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.06); } }
    @keyframes cloudFloat { from { transform: translateX(0); } to { transform: translateX(120vw); } }
    @keyframes rainDown { from { transform: translateY(-50px) rotate(15deg); } to { transform: translateY(105vh) rotate(15deg); } }
    @keyframes lightningFlash { 0%, 92%, 100% { opacity: 0; } 94%, 96% { opacity: 0.9; } }
    @keyframes stormBgFlash { 0%, 92%, 100% { filter: brightness(1); } 94%, 96% { filter: brightness(1.35); } }
    @keyframes snowDown { from { transform: translateY(-40px) rotate(0deg); } to { transform: translateY(105vh) rotate(360deg); } }
    </style>
    """
)


# ============================================================
# FULL-PAGE WEATHER BACKGROUND
# ============================================================

def render_background_animation(weather_type: str):
    if weather_type == "sunny":
        html = """
        <div id="weather-bg-container" class="bg-sunny">
            <div class="bg-sun"></div>
            <div class="bg-cloud cloud-pos-1"></div>
        </div>
        """
    elif weather_type == "cloudy":
        html = """
        <div id="weather-bg-container" class="bg-cloudy">
            <div class="bg-cloud cloud-pos-1"></div>
            <div class="bg-cloud cloud-pos-2"></div>
        </div>
        """
    elif weather_type == "rain":
        drops = "".join([f'<div class="bg-rain-drop" style="left: {i*8}%; animation-delay: {(i%5)*0.18}s;"></div>' for i in range(13)])
        html = f"""
        <div id="weather-bg-container" class="bg-rain">
            <div class="bg-cloud cloud-pos-1"></div>
            {drops}
        </div>
        """
    elif weather_type == "storm":
        drops = "".join([f'<div class="bg-rain-drop" style="left: {i*8}%; animation-delay: {(i%5)*0.15}s;"></div>' for i in range(13)])
        html = f"""
        <div id="weather-bg-container" class="bg-storm">
            <div class="bg-lightning">⚡</div>
            <div class="bg-cloud cloud-pos-1"></div>
            {drops}
        </div>
        """
    elif weather_type == "snow":
        flakes = "".join([f'<div class="bg-snowflake" style="left: {i*10}%; animation-delay: {(i%4)*0.8}s;">❄</div>' for i in range(10)])
        html = f"""
        <div id="weather-bg-container" class="bg-snow">
            {flakes}
        </div>
        """
    elif weather_type == "fog":
        html = """
        <div id="weather-bg-container" class="bg-fog">
            <div class="bg-cloud cloud-pos-1" style="filter: blur(15px); width: 80vw; height: 180px;"></div>
        </div>
        """
    else:
        html = '<div id="weather-bg-container" class="bg-default"></div>'
    render_html(html)


# ============================================================
# INITIAL OR DYNAMIC BACKGROUND
# ============================================================

if st.session_state.weather_result:
    current_weather_code = st.session_state.weather_result["current_weather"]["weather_code"]
    render_background_animation(get_weather_type(current_weather_code))
else:
    render_background_animation("default")


# ============================================================
# HEADER
# ============================================================

render_html(
    """
    <div class="weather-header">
        <div class="weather-title">🌤️ Weather Buddy</div>
        <div class="weather-subtitle">Intelligent, animated weather insights powered by Gemini</div>
    </div>
    """
)


# ============================================================
# SEARCH FORM
# ============================================================

with st.form("search_form"):
    location = st.text_input(
        "Location",
        placeholder="Enter city (e.g. Asansol, London, Tokyo)...",
        label_visibility="collapsed"
    )
    search_button = st.form_submit_button(
        "✨ Discover Weather",
        type="primary",
        use_container_width=True,
    )

if search_button:
    if not location.strip():
        st.warning("Please enter a city or location.")
    else:
        with st.spinner(f"Fetching skies above {location.strip()}..."):
            try:
                result = weather_graph.invoke({"location": location.strip()})
                st.session_state.weather_result = result
                st.session_state.shown_sections = []
                st.rerun()
            except Exception as e:
                st.error(f"Unable to fetch weather: {e}")
                st.stop()


# ============================================================
# DISPLAY WEATHER
# ============================================================

if st.session_state.weather_result:
    result = st.session_state.weather_result
    current = result["current_weather"]

    # Location Header Card
    state_display = f"{result['state']}, " if result.get("state") else ""
    render_html(
        f"""
        <div class="location-card">
            <div class="location-title">📍 {result["location_name"]}, {state_display}{result["country"]}</div>
            <div class="location-details">🕒 {result["timezone"]} &nbsp;•&nbsp; 🌐 {result["latitude"]}, {result["longitude"]}</div>
        </div>
        """
    )

    # Metrics Row 1
    render_html('<div class="section-title">🌡️ Current Conditions</div>')
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Temperature", f"{current['temperature']} °C")
    with c2:
        st.metric("Feels Like", f"{current['feels_like']} °C")
    with c3:
        st.metric("Humidity", f"{current['humidity']}%")
    with c4:
        st.metric("Condition", current["condition"])

    # Metrics Row 2
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("💨 Wind Speed", f"{current['wind_speed']} km/h")
    with c2:
        st.metric("🌬️ Gusts", f"{current['wind_gusts']} km/h")
    with c3:
        st.metric("🧭 Pressure", f"{current['pressure']} hPa")
    with c4:
        st.metric("☁️ Cloud Cover", f"{current['cloud_cover']}%")

    # ========================================================
    # FULL-WIDTH AI CARDS
    # ========================================================
    render_html('<div class="section-title">✨ AI Weather Analysis</div>')
    render_full_width_ai_cards(result["response"])

    st.divider()

    # Additional Forecasts
    sections = [
        ("hourly", "🕐 Today's Hourly Forecast"),
        ("daily", "📅 5-Day Outlook"),
        ("sun", "🌅 Sunrise & Sunset"),
    ]

    for section in st.session_state.shown_sections:
        if section == "hourly":
            render_html('<div class="section-title">🕐 Hourly Breakdown</div>')
            hourly = result["hourly_forecast"]
            hourly_table = [
                {
                    "Time": hour["time"],
                    "Temp": f"{hour['temperature']} °C",
                    "Feels Like": f"{hour['feels_like']} °C",
                    "Rain %": f"{hour['rain_probability']}%",
                    "Condition": hour["condition"],
                    "Humidity": f"{hour['humidity']}%",
                    "Wind": f"{hour['wind_speed']} km/h",
                }
                for hour in hourly[:24]
            ]
            st.dataframe(hourly_table, use_container_width=True, hide_index=True)

        elif section == "daily":
            render_html('<div class="section-title">📅 5-Day Outlook</div>')
            daily = result["daily_forecast"]
            daily_table = [
                {
                    "Date": day["date"],
                    "Weather": day["condition"],
                    "High": f"{day['high_temperature']} °C",
                    "Low": f"{day['low_temperature']} °C",
                    "Rain Chance": f"{day['rain_probability']}%",
                    "Precipitation": f"{day['precipitation']} mm",
                }
                for day in daily
            ]
            st.dataframe(daily_table, use_container_width=True, hide_index=True)

        elif section == "sun":
            render_html('<div class="section-title">🌅 Sunrise & Sunset</div>')
            today = result["daily_forecast"][0]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🌅 Sunrise", today["sunrise"])
            with col2:
                st.metric("🌇 Sunset", today["sunset"])

    # More Details Section
    remaining_sections = [
        s for s in sections if s[0] not in st.session_state.shown_sections
    ]

    if remaining_sections:
        render_html('<div class="section-title">🎯 More Forecast Details</div>')
        cols = st.columns(len(remaining_sections))
        for col, (section_id, label) in zip(cols, remaining_sections):
            with col:
                if st.button(label, key=f"btn_{section_id}", use_container_width=True):
                    st.session_state.shown_sections.append(section_id)
                    st.rerun()


# ============================================================
# FOOTER
# ============================================================

render_html(
    """
    <div style="text-align: center; color: #64748b; font-size: 0.88rem; margin-top: 3.5rem; font-weight: 600;">
        Powered with ❤️ by Open-Meteo & Gemini AI
    </div>
    """
)