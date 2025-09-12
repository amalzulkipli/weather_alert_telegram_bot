# Weather Alert Telegram Bot

A Python bot that monitors weather forecasts and sends Telegram notifications when rain is expected in your area.

## Features

- 🌧️ Monitors weather forecasts for the next 48 hours
- 📱 Sends automated Telegram notifications when rain is predicted
- 🕐 Displays rain predictions with time and weather emoji
- 🌍 Configurable location coordinates
- ⏰ Designed to run periodically (e.g., via cron job)

## Prerequisites

- Python 3.7 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenWeatherMap API Key (free tier available at [openweathermap.org](https://openweathermap.org/api))
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
OPENWEATHER_API_KEY=your_openweather_api_key
TELEGRAM_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
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

### Getting OpenWeatherMap API Key
1. Sign up at [openweathermap.org](https://openweathermap.org/api)
2. Navigate to your API keys section
3. Copy your API key

### Setting Your Location
- Find your location's latitude and longitude
- You can use [latlong.net](https://www.latlong.net/) or Google Maps
- Add these coordinates to your `.env` file

## Usage

### Manual Run
```bash
python main.py
```

### Automated Scheduling with Cron
To run the bot automatically every morning at 6 AM:

1. Open your crontab:
```bash
crontab -e
```

2. Add this line:
```bash
0 6 * * * cd /path/to/weather_alert_telegram_bot && /path/to/.venv/bin/python main.py
```

### Example Output
When rain is detected, you'll receive a Telegram message like:
```
🌧️ Rain Alert! 🌧️

📅 Today (Monday)
• 09:00 AM - 🌧️ Light rain
• 12:00 PM - 🌧️ Light rain
• 03:00 PM - 🌦️ Light rain

📅 Tomorrow (Tuesday)
• 06:00 AM - 🌧️ Moderate rain
```

## How It Works

1. The bot fetches a 5-day weather forecast from OpenWeatherMap API
2. Filters the forecast for the next 48 hours
3. Checks for any rain predictions
4. If rain is found, formats a message with times and weather conditions
5. Sends the notification to your Telegram chat

## Weather Icons

The bot converts weather conditions to emoji for better readability:
- ☀️ Clear sky
- ☁️ Cloudy
- 🌧️ Rain
- 🌩️ Thunderstorm
- 🌨️ Snow
- 🌫️ Mist/Fog

## Troubleshooting

### No notifications received
- Verify your bot token and chat ID are correct
- Check if the bot has permission to send messages to your chat
- Ensure your location coordinates are valid
- Run the script manually to check for errors

### API errors
- Verify your OpenWeatherMap API key is valid
- Check if you've exceeded the API rate limit
- Ensure you have an active internet connection

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the [MIT License](LICENSE).