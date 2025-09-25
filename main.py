import requests
import datetime
import os
import argparse
from dotenv import load_dotenv
from collections import defaultdict
load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Hybrid Weather Bot: MET Malaysia + WeatherAPI.com')
parser.add_argument('--mode', choices=['daily', 'alert'], default='daily',
                    help='Mode: daily (MET Malaysia) or alert (WeatherAPI.com)')
args = parser.parse_args()

# === CONFIG ===
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")  # For 30-min alerts
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # Fallback API
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") 
LAT, LON = float(os.getenv("LAT")), float(os.getenv("LON"))

print(f"Mode: {args.mode}")
print(f"Coordinates: {LAT}, {LON}")

class METMalaysiaAPI:
    """Handler for MET Malaysia API - for daily forecasts"""
    
    def __init__(self):
        self.base_url = "https://api.data.gov.my/weather/forecast"
        self.rain_conditions = {
            "tiada hujan": {"en": "No rain", "has_rain": False, "icon": "☀️"},
            "hujan": {"en": "Rain", "has_rain": True, "icon": "🌧"},
            "hujan di beberapa tempat": {"en": "Scattered rain", "has_rain": True, "icon": "🌦"},
            "hujan di satu dua tempat": {"en": "Isolated rain", "has_rain": True, "icon": "🌦"},
            "ribut petir": {"en": "Thunderstorms", "has_rain": True, "icon": "⛈"},
            "ribut petir di beberapa tempat": {"en": "Scattered thunderstorms", "has_rain": True, "icon": "⛈"},
            "ribut petir di satu dua tempat": {"en": "Isolated thunderstorms", "has_rain": True, "icon": "⛈"},
            "berjerebu": {"en": "Hazy", "has_rain": False, "icon": "🌫"}
        }
    
    def get_sepang_forecast(self):
        """Get Sepang forecast from MET Malaysia"""
        try:
            # Filter for Sepang specifically
            url = f"{self.base_url}?contains=Sepang@location__location_name"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"MET Malaysia API error: {e}")
            return []
    
    def parse_daily_rain(self, data):
        """Parse MET Malaysia data for daily rain forecast"""
        today = datetime.datetime.now().date()
        tomorrow = today + datetime.timedelta(days=1)
        rain_by_date = defaultdict(list)
        
        # Find Sepang District data (prioritize Ds over Tn)
        selected_location = None
        for item in data:
            if ("sepang" in item['location']['location_name'].lower() and 
                item['location']['location_id'].startswith('Ds')):
                selected_location = item
                break
        
        if not selected_location and data:
            # Fallback to any Sepang location
            for item in data:
                if "sepang" in item['location']['location_name'].lower():
                    selected_location = item
                    break
        
        if not selected_location:
            return rain_by_date, today, tomorrow, "No location found"
        
        print(f"Using: {selected_location['location']['location_name']} ({selected_location['location']['location_id']})")
        
        # Process forecasts for selected location only
        for item in data:
            if (item['location']['location_name'] == selected_location['location']['location_name'] and 
                item['location']['location_id'] == selected_location['location']['location_id']):
                
                forecast_date = datetime.datetime.strptime(item['date'], "%Y-%m-%d").date()
                
                if forecast_date in (today, tomorrow):
                    periods = [
                        ("5 AM", item.get('morning_forecast', '').lower()),
                        ("2 PM", item.get('afternoon_forecast', '').lower()),
                        ("8 PM", item.get('night_forecast', '').lower())
                    ]
                    
                    for time_period, condition in periods:
                        condition_info = self.rain_conditions.get(condition, {
                            "en": condition.title(), 
                            "has_rain": "hujan" in condition or "ribut" in condition, 
                            "icon": "🌧" if "hujan" in condition or "ribut" in condition else "☁️"
                        })
                        
                        if condition_info["has_rain"]:
                            rain_by_date[forecast_date].append({
                                "time": time_period,
                                "description": condition_info["en"],
                                "icon": condition_info["icon"],
                                "date": forecast_date
                            })
        
        return rain_by_date, today, tomorrow, selected_location['location']['location_name']

class WeatherAPIClient:
    """Handler for WeatherAPI.com - for immediate alerts"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.weatherapi.com/v1"
        self.weather_icons = {
            1000: "☀️", 1003: "⛅", 1006: "☁️", 1009: "☁️",
            1030: "🌫", 1063: "🌦", 1180: "🌦", 1183: "🌧",
            1186: "🌧", 1189: "🌧", 1192: "🌧", 1195: "🌧",
            1240: "🌦", 1243: "🌧", 1246: "🌧", 1273: "⛈",
            1276: "⛈", 1087: "⛈"
        }
    
    def get_hourly_forecast(self):
        """Get hourly forecast for next few hours"""
        try:
            url = f"{self.base_url}/forecast.json?key={self.api_key}&q={LAT},{LON}&hours=6&aqi=no"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"WeatherAPI error: {e}")
            return None
    
    def parse_30min_alerts(self, data):
        """Parse WeatherAPI data for 30-minute alerts"""
        if not data:
            return []
        
        now = datetime.datetime.now()
        cutoff_time = now + datetime.timedelta(minutes=30)
        rain_alerts = []
        
        for hour in data["forecast"]["forecastday"][0]["hour"]:
            dt = datetime.datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
            
            # Check if forecast is within next 30 minutes
            if now <= dt <= cutoff_time:
                will_rain = (
                    hour["will_it_rain"] == 1 or 
                    hour["chance_of_rain"] >= 60 or  # Higher threshold for alerts
                    "rain" in hour["condition"]["text"].lower()
                )
                
                if will_rain:
                    time_str = dt.strftime("%I:%M %p").lstrip("0")
                    description = hour["condition"]["text"]
                    icon = self.weather_icons.get(hour["condition"]["code"], "🌧")
                    
                    rain_alerts.append({
                        "time": time_str,
                        "description": description,
                        "icon": icon,
                        "datetime": dt,
                        "chance": hour["chance_of_rain"]
                    })
        
        return rain_alerts

class OpenWeatherFallback:
    """Fallback API using OpenWeatherMap"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.weather_icons = {
            "01d": "☀️", "01n": "🌙", "02d": "⛅", "02n": "⛅",
            "03d": "☁️", "03n": "☁️", "04d": "☁️", "04n": "☁️",
            "09d": "🌧", "09n": "🌧", "10d": "🌦", "10n": "🌦",
            "11d": "⛈", "11n": "⛈", "13d": "❄️", "13n": "❄️",
            "50d": "🌫", "50n": "🌫"
        }
    
    def get_daily_forecast(self):
        """Get 5-day forecast from OpenWeatherMap"""
        try:
            url = f"{self.base_url}/forecast?lat={LAT}&lon={LON}&appid={self.api_key}&units=metric"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"OpenWeatherMap API error: {e}")
            return None
    
    def get_current_weather(self):
        """Get current weather from OpenWeatherMap"""
        try:
            url = f"{self.base_url}/weather?lat={LAT}&lon={LON}&appid={self.api_key}&units=metric"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"OpenWeatherMap current API error: {e}")
            return None
    
    def parse_daily_rain_fallback(self, data):
        """Parse OpenWeatherMap data for daily rain forecast"""
        if not data:
            return []
        
        today = datetime.datetime.now().date()
        tomorrow = today + datetime.timedelta(days=1)
        rain_by_date = defaultdict(list)
        
        for item in data["list"]:
            dt = datetime.datetime.fromtimestamp(item["dt"]).date()
            
            if dt in (today, tomorrow):
                # Check if it will rain
                weather = item["weather"][0]
                will_rain = (
                    "rain" in weather["main"].lower() or 
                    "drizzle" in weather["main"].lower() or
                    "thunderstorm" in weather["main"].lower()
                )
                
                if will_rain:
                    time_obj = datetime.datetime.fromtimestamp(item["dt"])
                    time_str = time_obj.strftime("%I:%M %p").lstrip("0")
                    description = weather["description"].title()
                    icon = self.weather_icons.get(weather["icon"], "🌧")
                    
                    rain_by_date[dt].append({
                        "time": time_str,
                        "description": description,
                        "icon": icon,
                        "date": dt
                    })
        
        return rain_by_date, today, tomorrow
    
    def parse_30min_alerts_fallback(self, current_data):
        """Parse OpenWeatherMap for immediate alerts (basic fallback)"""
        if not current_data:
            return []
        
        rain_alerts = []
        weather = current_data["weather"][0]
        
        # Check if it's currently raining or about to rain
        will_rain = (
            "rain" in weather["main"].lower() or 
            "drizzle" in weather["main"].lower() or
            "thunderstorm" in weather["main"].lower()
        )
        
        if will_rain:
            now = datetime.datetime.now()
            time_str = now.strftime("%I:%M %p").lstrip("0")
            description = weather["description"].title()
            icon = self.weather_icons.get(weather["icon"], "🌧")
            
            rain_alerts.append({
                "time": f"Now ({time_str})",
                "description": description,
                "icon": icon,
                "datetime": now
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
    print(f"Telegram response: {tg_response.status_code}")
    return tg_response

# === Main execution based on mode ===
if args.mode == 'daily':
    print("🏛️ Using MET Malaysia API for daily forecast...")
    
    met_api = METMalaysiaAPI()
    data = met_api.get_sepang_forecast()
    
    if data:
        rain_by_date, today, tomorrow, location = met_api.parse_daily_rain(data)
        
        # Always show both Today and Tomorrow sections
        msg_parts = ["☔ Daily Rain Report"]
        
        # Today section
        msg_parts.append(f"\n*Today* *({today.strftime('%Y-%m-%d')})*")
        if today in rain_by_date:
            msg_parts.append("Expected rain at:")
            for forecast in rain_by_date[today]:
                msg_parts.append(f"  • {forecast['time']} - {forecast['description']} {forecast['icon']}")
        else:
            msg_parts.append("No rain predicted")
        
        # Tomorrow section
        msg_parts.append(f"\n*Tomorrow* *({tomorrow.strftime('%Y-%m-%d')})*")
        if tomorrow in rain_by_date:
            msg_parts.append("Expected rain at:")
            for forecast in rain_by_date[tomorrow]:
                msg_parts.append(f"  • {forecast['time']} - {forecast['description']} {forecast['icon']}")
        else:
            msg_parts.append("No rain predicted")
        
        msg = "\n".join(msg_parts)
        send_telegram_message(msg)
        print("Daily rain report sent via Telegram!")
    else:
        # Fallback to OpenWeatherMap
        print("⚠️ MET Malaysia failed, trying OpenWeatherMap fallback...")
        
        if not OPENWEATHER_API_KEY:
            print("❌ OPENWEATHER_API_KEY not found in environment variables.")
            msg = "❌ Unable to fetch weather data. Both primary and fallback APIs are unavailable."
            send_telegram_message(msg)
        else:
            openweather_api = OpenWeatherFallback(OPENWEATHER_API_KEY)
            fallback_data = openweather_api.get_daily_forecast()
            
            if fallback_data:
                rain_by_date, today, tomorrow = openweather_api.parse_daily_rain_fallback(fallback_data)
                
                # Always show both Today and Tomorrow sections (fallback)
                msg_parts = ["☔ Daily Rain Report"]
                
                # Today section
                msg_parts.append(f"\n*Today* *({today.strftime('%Y-%m-%d')})*")
                if today in rain_by_date:
                    msg_parts.append("Expected rain at:")
                    for forecast in rain_by_date[today]:
                        msg_parts.append(f"  • {forecast['time']} - {forecast['description']} {forecast['icon']}")
                else:
                    msg_parts.append("No rain predicted")
                
                # Tomorrow section
                msg_parts.append(f"\n*Tomorrow* *({tomorrow.strftime('%Y-%m-%d')})*")
                if tomorrow in rain_by_date:
                    msg_parts.append("Expected rain at:")
                    for forecast in rain_by_date[tomorrow]:
                        msg_parts.append(f"  • {forecast['time']} - {forecast['description']} {forecast['icon']}")
                else:
                    msg_parts.append("No rain predicted")
                
                msg = "\n".join(msg_parts)
                send_telegram_message(msg)
                print("Daily rain report sent via Telegram (OpenWeatherMap fallback)!")
            else:
                msg = "❌ Unable to fetch weather data. Both primary and fallback APIs failed."
                send_telegram_message(msg)
                print("Both MET Malaysia and OpenWeatherMap failed.")

elif args.mode == 'alert':
    print("🌐 Using WeatherAPI.com for 30-minute alerts...")
    
    if not WEATHERAPI_KEY:
        print("❌ WEATHERAPI_KEY not found in environment variables.")
        exit(1)
    
    weather_api = WeatherAPIClient(WEATHERAPI_KEY)
    data = weather_api.get_hourly_forecast()
    
    if data:
        rain_alerts = weather_api.parse_30min_alerts(data)
        
        if rain_alerts:
            # Simple, single-line format for rain alerts
            rain_descriptions = []
            for alert in rain_alerts:
                chance_str = f" ({alert['chance']}%)" if 'chance' in alert else ""
                rain_descriptions.append(f"{alert['description']}{chance_str} {alert['icon']}")
            
            # Join multiple alerts with " | "
            combined_description = " | ".join(rain_descriptions)
            msg = f"🚨 Immediate Rain Alert!\nRain expected in the next 30 minutes | {combined_description}"
            
            send_telegram_message(msg)
            print("30-minute rain alert sent via Telegram!")
        else:
            print("No rain expected in the next 30 minutes.")
    else:
        # Fallback to OpenWeatherMap
        print("⚠️ WeatherAPI failed, trying OpenWeatherMap fallback...")
        
        if not OPENWEATHER_API_KEY:
            print("❌ OPENWEATHER_API_KEY not found in environment variables.")
            msg = "❌ Unable to fetch weather alert data. Both primary and fallback APIs are unavailable."
            send_telegram_message(msg)
        else:
            openweather_api = OpenWeatherFallback(OPENWEATHER_API_KEY)
            fallback_data = openweather_api.get_current_weather()
            
            if fallback_data:
                rain_alerts = openweather_api.parse_30min_alerts_fallback(fallback_data)
                
                if rain_alerts:
                    # Simple, single-line format for fallback alerts
                    rain_descriptions = []
                    for alert in rain_alerts:
                        rain_descriptions.append(f"{alert['description']} {alert['icon']}")
                    
                    # Join multiple alerts with " | "
                    combined_description = " | ".join(rain_descriptions)
                    msg = f"� Current Weather Alert!\nRain conditions detected | {combined_description}"
                    
                    send_telegram_message(msg)
                    print("Weather alert sent via Telegram (OpenWeatherMap fallback)!")
                else:
                    print("No immediate rain detected (fallback check).")
            else:
                msg = "❌ Unable to fetch weather alert data. Both primary and fallback APIs failed."
                send_telegram_message(msg)
                print("Both WeatherAPI and OpenWeatherMap failed.")

print(f"Weather check completed in {args.mode} mode.")