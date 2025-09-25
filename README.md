# We## Features

- 🏛️ **Dual Mode Operation**: Daily reports and 30-minute alerts
- 🌧️ **Hybrid API Architecture**: Uses multiple weather services for optimal accuracy
- 📱 **Smart Telegram Notifications**: Markdown-formatted messages with weather emojis
- 🇲🇾 **Malaysia-Optimized**: Official MET Malaysia data for local accuracy
- 🔄 **Automatic Fallbacks**: OpenWeatherMap backup when primary APIs fail
- 📍 **Location-Specific**: Precisely targeted for Sepang/Salak Tinggi area
- ⏰ **Cron-Ready**: Designed for automated scheduling
- 📝 **Professional Logging**: Structured logs with rotation and component trackingrt Telegram Bot

A Python bot that monitors weather forecasts and sends Telegram notifications when rain is expected in your area. Features a hybrid architecture with multiple weather APIs and intelligent fallbacks for maximum reliability.

## Features

- �️ **Dual Mode Operation**: Daily reports and 30-minute alerts
- 🌧️ **Hybrid API Architecture**: Uses multiple weather services for optimal accuracy
- 📱 **Smart Telegram Notifications**: Markdown-formatted messages with weather emojis
- 🇲🇾 **Malaysia-Optimized**: Official MET Malaysia data for local accuracy
- 🔄 **Automatic Fallbacks**: OpenWeatherMap backup when primary APIs fail
- 📍 **Location-Specific**: Precisely targeted for Sepang/Salak Tinggi area
- ⏰ **Cron-Ready**: Designed for automated scheduling

## Architecture

### Primary APIs
- **Daily Mode**: MET Malaysia Government API (official meteorological data)
- **Alert Mode**: WeatherAPI.com (real-time 30-minute forecasts)

### Fallback API
- **OpenWeatherMap**: Automatic backup for both modes when primary APIs fail

## Prerequisites

- Python 3.7 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- WeatherAPI.com API Key (free tier at [weatherapi.com](https://www.weatherapi.com/))
- OpenWeatherMap API Key (free tier at [openweathermap.org](https://openweathermap.org/api))
- Telegram Chat ID (where notifications will be sent)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/amalzulkipli/weather_alert_telegram_bot.git
cd weather_alert_telegram_bot
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
TELEGRAM_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
WEATHERAPI_KEY=your_weatherapi_key
OPENWEATHER_API_KEY=your_openweather_api_key
LAT=your_latitude
LON=your_longitude
```

## Configuration

### Getting Your Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token provided

### Getting Your Chat ID
1. Add your bot to a channel or start a conversation with it
2. Send a message to the bot
3. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your chat ID in the response

### Getting WeatherAPI.com API Key
1. Sign up at [weatherapi.com](https://www.weatherapi.com/)
2. Navigate to your API keys section
3. Copy your API key

### Getting OpenWeatherMap API Key
1. Sign up at [openweathermap.org](https://openweathermap.org/api)
2. Navigate to your API keys section
3. Copy your API key

### Setting Your Location
- Find your location's latitude and longitude
- You can use [latlong.net](https://www.latlong.net/) or Google Maps
- Add these coordinates to your `.env` file

## Usage

### Daily Report Mode (Default)
```bash
python main.py --mode daily
# or simply
python main.py
```

### 30-Minute Alert Mode
```bash
python main.py --mode alert
```

### Automated Scheduling with Cron

**Daily Reports (7 AM)**
```bash
0 7 * * * cd /path/to/weather_alert_telegram_bot && /path/to/.venv/bin/python main.py --mode daily
```

**30-Minute Rain Alerts (Work Hours)**
```bash
*/30 8-18 * * 1-5 cd /path/to/weather_alert_telegram_bot && /path/to/.venv/bin/python main.py --mode alert
```

### Example Output

**Daily Report:**
```
☔ Daily Rain Report

*Today* *(2025-09-25)*
Expected rain at:
  • 5 AM - Scattered rain 🌦
  • 2 PM - Light rain 🌧

*Tomorrow* *(2025-09-26)*
No rain predicted
```

**Rain Alert:**
```
🚨 Immediate Rain Alert!
Rain expected in the next 30 minutes | Light rain (75%) 🌧
```

## How It Works

### Daily Mode
1. Queries MET Malaysia government API for official forecast data
2. Filters specifically for Sepang area (District prioritized over Town)  
3. Checks today and tomorrow for rain predictions
4. Falls back to OpenWeatherMap if MET Malaysia is unavailable
5. Sends formatted report with time periods and weather conditions

### Alert Mode  
1. Uses WeatherAPI.com for real-time hourly forecasts
2. Analyzes next 30 minutes for immediate rain probability
3. Falls back to OpenWeatherMap current conditions if primary API fails
4. Sends immediate alerts only when rain is imminent

### Fallback System
- **Automatic Detection**: APIs failures are automatically detected
- **Seamless Switching**: Falls back to OpenWeatherMap without user intervention  
- **Clear Labeling**: Fallback messages are clearly marked in notifications
- **Comprehensive Coverage**: Both modes have fallback protection

## API Sources

| Mode | Primary API | Fallback API | Accuracy |
|------|-------------|--------------|----------|
| Daily | MET Malaysia | OpenWeatherMap | Government-grade |
| Alert | WeatherAPI.com | OpenWeatherMap | Real-time precision |

## Weather Icons

The bot converts weather conditions to emoji for better readability:
- ☀️ Clear sky / No rain
- ⛅ Partly cloudy  
- ☁️ Cloudy
- 🌦 Scattered rain
- 🌧 Rain / Light rain
- ⛈ Thunderstorms
- � Hazy / Mist

## Logging

The bot features a professional logging system designed for production deployment:

### Log Files
- **Location**: `logs/weather_bot.log`
- **Rotation**: Automatically rotates when logs exceed 10MB (keeps 5 files)
- **Format**: `YYYY-MM-DD HH:MM:SS | LEVEL | COMPONENT | MESSAGE`

### Viewing Logs
```bash
# View recent logs
python view_logs.py

# View last 20 lines
python view_logs.py --lines 20

# Filter by component
python view_logs.py --component telegram
python view_logs.py --component met-api

# Filter by level
python view_logs.py --level ERROR

# Follow logs in real-time (like tail -f)
python view_logs.py --follow
```

### Log Components
- **main**: Application startup, mode selection, and completion
- **met-api**: MET Malaysia API requests and responses
- **weather-api**: WeatherAPI.com requests and responses  
- **openweather**: OpenWeatherMap fallback API activity
- **telegram**: Telegram message delivery status

### Example Log Output
```
2025-09-25 08:15:00 | INFO  | main        | Starting daily mode (coordinates: 2.8389, 101.6957)
2025-09-25 08:15:00 | INFO  | met-api     | MET Malaysia API request successful (200)
2025-09-25 08:15:00 | INFO  | met-api     | Using location: Sepang (Ds064)
2025-09-25 08:15:01 | INFO  | telegram    | Message sent successfully
2025-09-25 08:15:01 | INFO  | main        | Daily report completed successfully
```

## Troubleshooting

### No notifications received
- Verify your bot token and chat ID are correct
- Check if the bot has permission to send messages to your chat
- Ensure your location coordinates are valid
- **Check logs**: `python view_logs.py --component telegram` to see message delivery status
- Verify API keys for all three services

### API errors
- The bot will automatically fall back to OpenWeatherMap if primary APIs fail
- **Check logs**: `python view_logs.py --level ERROR` to see API error details
- Check if you've exceeded any API rate limits
- Ensure you have an active internet connection
- Verify all API keys are valid and active

### Location issues
- MET Malaysia API filters specifically for "Sepang" in location names
- Coordinates should be precise for best results
- The bot prioritizes District (Ds) locations over Town (Tn) locations
- **Check logs**: `python view_logs.py --component met-api` to see location selection

### Debugging with logs
```bash
# Check recent activity
python view_logs.py --lines 20

# Monitor real-time execution
python view_logs.py --follow

# Check for errors only
python view_logs.py --level ERROR
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the [MIT License](LICENSE).