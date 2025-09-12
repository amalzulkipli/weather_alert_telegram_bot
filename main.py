import requests
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

# === CONFIG ===
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT, LON = float(os.getenv("LAT")), float(os.getenv("LON"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") 

# === Fetch forecast ===
url = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric"
response = requests.get(url)
data = response.json()
print(data)

from collections import defaultdict

# Weather icon mapping
WEATHER_ICONS = {
    "01d": "☀️", "01n": "🌙",  # clear sky
    "02d": "⛅", "02n": "☁️",  # few clouds
    "03d": "☁️", "03n": "☁️",  # scattered clouds
    "04d": "☁️", "04n": "☁️",  # broken clouds
    "09d": "🌧", "09n": "🌧",  # shower rain
    "10d": "🌦", "10n": "🌧",  # rain
    "11d": "⛈", "11n": "⛈",  # thunderstorm
    "13d": "🌨", "13n": "🌨",  # snow
    "50d": "🌫", "50n": "🌫",  # mist
}

# Get today and tomorrow's dates
today = datetime.datetime.now().date()
tomorrow = today + datetime.timedelta(days=1)

# Group forecasts by date
rain_by_date = defaultdict(list)

for forecast in data["list"]:
    dt = datetime.datetime.fromtimestamp(forecast["dt"])
    forecast_date = dt.date()
    weather_info = forecast["weather"][0]
    
    # Only check for rain today and tomorrow
    if forecast_date in (today, tomorrow) and "rain" in weather_info["main"].lower():
        # Convert to 12-hour format
        time_12h = dt.strftime("%I %p").lstrip("0")
        description = weather_info["description"].title()
        icon = WEATHER_ICONS.get(weather_info["icon"], "🌧")
        
        rain_by_date[forecast_date].append({
            "time": time_12h,
            "description": description,
            "icon": icon
        })

# === Send notification if rain found ===
if rain_by_date:
    msg_parts = ["☔ Rain Alert!"]
    
    for date, forecasts in rain_by_date.items():
        date_str = "Today" if date == today else "Tomorrow"
        msg_parts.append(f"\n*{date_str}* *({date.strftime('%Y-%m-%d')})*")
        msg_parts.append("Expected rain at: ")
        
        for i, forecast in enumerate(forecasts, 1):
            msg_parts.append(f"    {i}. {forecast['time']} - {forecast['description']} {forecast['icon']}")
    
    msg = "\n".join(msg_parts)
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    tg_response = requests.post(tg_url, data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })
    print("Rain alert sent via Telegram!")
else:
    print("No rain forecasted today.")
