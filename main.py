import requests
import datetime
import os
import argparse
from dotenv import load_dotenv
load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Weather bot with different modes')
parser.add_argument('--mode', choices=['daily', 'alert'], default='daily',
                    help='Mode: daily (today+tomorrow) or alert (next 30 minutes)')
args = parser.parse_args()

# === CONFIG ===
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT, LON = float(os.getenv("LAT")), float(os.getenv("LON"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") 

# === Fetch forecast ===
url = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric"
response = requests.get(url)
data = response.json()

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

def check_daily_rain():
    """Check rain for today and tomorrow (daily mode)"""
    today = datetime.datetime.now().date()
    tomorrow = today + datetime.timedelta(days=1)
    
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
                "icon": icon,
                "date": forecast_date
            })
    
    return rain_by_date, today, tomorrow

def check_30min_rain():
    """Check rain for the next 30 minutes (alert mode)"""
    now = datetime.datetime.now()
    cutoff_time = now + datetime.timedelta(minutes=30)
    
    rain_alerts = []
    
    for forecast in data["list"]:
        dt = datetime.datetime.fromtimestamp(forecast["dt"])
        weather_info = forecast["weather"][0]
        
        # Check if forecast is within next 30 minutes
        if now <= dt <= cutoff_time and "rain" in weather_info["main"].lower():
            time_12h = dt.strftime("%I:%M %p").lstrip("0")
            description = weather_info["description"].title()
            icon = WEATHER_ICONS.get(weather_info["icon"], "🌧")
            
            rain_alerts.append({
                "time": time_12h,
                "description": description,
                "icon": icon,
                "datetime": dt
            })
    
    return rain_alerts

def send_telegram_message(message):
    """Send message to Telegram"""
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    tg_response = requests.post(tg_url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })
    return tg_response

# === Main execution based on mode ===
if args.mode == 'daily':
    # Daily report mode (12:01 AM)
    rain_by_date, today, tomorrow = check_daily_rain()
    
    if rain_by_date:
        msg_parts = ["☔ Daily Rain Report"]
        
        for date, forecasts in rain_by_date.items():
            date_str = "Today" if date == today else "Tomorrow"
            msg_parts.append(f"\n*{date_str}* *({date.strftime('%Y-%m-%d')})*")
            msg_parts.append("Expected rain at: ")
            
            for i, forecast in enumerate(forecasts, 1):
                msg_parts.append(f"    {i}. {forecast['time']} - {forecast['description']} {forecast['icon']}")
        
        msg = "\n".join(msg_parts)
        send_telegram_message(msg)
        print("Daily rain report sent via Telegram!")
    else:
        msg = "☀️ Good news! No rain expected today or tomorrow."
        send_telegram_message(msg)
        print("Daily report sent: No rain expected.")
        
elif args.mode == 'alert':
    # 30-minute alert mode
    rain_alerts = check_30min_rain()
    
    if rain_alerts:
        msg_parts = ["🚨 Immediate Rain Alert!"]
        msg_parts.append("Rain expected in the next 30 minutes:")
        
        for i, alert in enumerate(rain_alerts, 1):
            msg_parts.append(f"    {i}. {alert['time']} - {alert['description']} {alert['icon']}")
        
        msg_parts.append("\n💡 Don't forget your umbrella!")
        
        msg = "\n".join(msg_parts)
        send_telegram_message(msg)
        print("30-minute rain alert sent via Telegram!")
    else:
        print("No rain expected in the next 30 minutes.")
