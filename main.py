import requests
import datetime
import os
import argparse
import logging
import logging.handlers
from dotenv import load_dotenv
from collections import defaultdict
load_dotenv()

# === LOGGING SETUP ===
def setup_logging():
    """Setup professional logging system for production deployment"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('weather_bot')
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-5s | %(name)-12s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (max 10MB, keep 5 files)
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/weather_bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler for critical errors only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logging
logger = setup_logging()

# Component-specific loggers
met_logger = logging.getLogger('weather_bot.met-api')
weather_logger = logging.getLogger('weather_bot.weather-api')
openweather_logger = logging.getLogger('weather_bot.openweather')
telegram_logger = logging.getLogger('weather_bot.telegram')
main_logger = logging.getLogger('weather_bot.main')

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

main_logger.info(f"Starting {args.mode} mode (coordinates: {LAT}, {LON})")

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
            met_logger.info(f"MET Malaysia API request successful ({response.status_code})")
            return response.json()
        except Exception as e:
            met_logger.error(f"MET Malaysia API failed: {e}")
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
            met_logger.warning("No Sepang location found in MET Malaysia data")
            return rain_by_date, today, tomorrow, "No location found"
        
        met_logger.info(f"Using location: {selected_location['location']['location_name']} ({selected_location['location']['location_id']})")
        
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
            weather_logger.info(f"WeatherAPI request successful ({response.status_code})")
            return response.json()
        except Exception as e:
            weather_logger.error(f"WeatherAPI failed: {e}")
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
            openweather_logger.info(f"OpenWeather forecast API successful ({response.status_code})")
            return response.json()
        except Exception as e:
            openweather_logger.error(f"OpenWeather forecast API failed: {e}")
            return None
    
    def get_current_weather(self):
        """Get current weather from OpenWeatherMap"""
        try:
            url = f"{self.base_url}/weather?lat={LAT}&lon={LON}&appid={self.api_key}&units=metric"
            response = requests.get(url)
            response.raise_for_status()
            openweather_logger.info(f"OpenWeather current API successful ({response.status_code})")
            return response.json()
        except Exception as e:
            openweather_logger.error(f"OpenWeather current API failed: {e}")
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
    
    if tg_response.status_code == 200:
        telegram_logger.info("Message sent successfully")
    else:
        telegram_logger.error(f"Message failed to send (HTTP {tg_response.status_code})")
    
    return tg_response

# === Main execution based on mode ===
if args.mode == 'daily':
    main_logger.info("Starting daily forecast mode using MET Malaysia API")
    
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
            main_logger.info(f"Rain forecast found for today: {len(rain_by_date[today])} periods")
        else:
            msg_parts.append("No rain predicted")
            main_logger.info("No rain predicted for today")
        
        # Tomorrow section
        msg_parts.append(f"\n*Tomorrow* *({tomorrow.strftime('%Y-%m-%d')})*")
        if tomorrow in rain_by_date:
            msg_parts.append("Expected rain at:")
            for forecast in rain_by_date[tomorrow]:
                msg_parts.append(f"  • {forecast['time']} - {forecast['description']} {forecast['icon']}")
            main_logger.info(f"Rain forecast found for tomorrow: {len(rain_by_date[tomorrow])} periods")
        else:
            msg_parts.append("No rain predicted")
            main_logger.info("No rain predicted for tomorrow")
        
        msg = "\n".join(msg_parts)
        send_telegram_message(msg)
        main_logger.info("Daily report completed successfully")
    else:
        # Fallback to OpenWeatherMap
        main_logger.warning("MET Malaysia API failed, attempting OpenWeatherMap fallback")
        
        if not OPENWEATHER_API_KEY:
            main_logger.error("OpenWeatherMap API key not configured")
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
                    main_logger.info(f"Fallback: Rain forecast found for today: {len(rain_by_date[today])} periods")
                else:
                    msg_parts.append("No rain predicted")
                    main_logger.info("Fallback: No rain predicted for today")
                
                # Tomorrow section
                msg_parts.append(f"\n*Tomorrow* *({tomorrow.strftime('%Y-%m-%d')})*")
                if tomorrow in rain_by_date:
                    msg_parts.append("Expected rain at:")
                    for forecast in rain_by_date[tomorrow]:
                        msg_parts.append(f"  • {forecast['time']} - {forecast['description']} {forecast['icon']}")
                    main_logger.info(f"Fallback: Rain forecast found for tomorrow: {len(rain_by_date[tomorrow])} periods")
                else:
                    msg_parts.append("No rain predicted")
                    main_logger.info("Fallback: No rain predicted for tomorrow")
                
                msg = "\n".join(msg_parts)
                send_telegram_message(msg)
                main_logger.info("Daily report completed using OpenWeatherMap fallback")
            else:
                main_logger.error("Both MET Malaysia and OpenWeatherMap APIs failed")
                msg = "❌ Unable to fetch weather data. Both primary and fallback APIs failed."
                send_telegram_message(msg)

elif args.mode == 'alert':
    main_logger.info("Starting alert mode using WeatherAPI.com")
    
    if not WEATHERAPI_KEY:
        main_logger.error("WeatherAPI key not configured")
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
            main_logger.info(f"30-minute rain alert sent ({len(rain_alerts)} alerts)")
        else:
            main_logger.info("No rain expected in next 30 minutes")
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
                    main_logger.info(f"Weather alert sent using OpenWeatherMap fallback ({len(rain_alerts)} alerts)")
                else:
                    main_logger.info("Fallback: No immediate rain detected")
            else:
                main_logger.error("Both WeatherAPI and OpenWeatherMap APIs failed")
                msg = "❌ Unable to fetch weather alert data. Both primary and fallback APIs failed."
                send_telegram_message(msg)

main_logger.info(f"Weather check completed in {args.mode} mode")