# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Python-based weather forecast bot that checks for rain predictions and sends notifications via Telegram. The bot fetches weather data from OpenWeatherMap API and notifies users when rain is expected within the next 48 hours.

## Development Commands

### Running the Bot
```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run daily report mode (default - checks today and tomorrow)
python main.py --mode daily
# or simply
python main.py

# Run 30-minute alert mode (checks next 30 minutes only)
python main.py --mode alert
```

### Testing and Validation
```bash
# Verify environment variables are set
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Config OK' if all([os.getenv('OPENWEATHER_API_KEY'), os.getenv('TELEGRAM_TOKEN'), os.getenv('CHAT_ID')]) else 'Missing config')"

# Test weather API connection
python -c "import requests; import os; from dotenv import load_dotenv; load_dotenv(); r = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?lat={os.getenv('LAT')}&lon={os.getenv('LON')}&appid={os.getenv('OPENWEATHER_API_KEY')}&units=metric'); print(f'Weather API: {r.status_code}')"

# Dry run (check weather without sending notification)
# Note: Currently not supported - bot always sends if rain detected
```

### Common Development Tasks
```bash
# Create/update virtual environment
python -m venv .venv
source .venv/bin/activate

# Install new dependencies
pip install <package-name>
pip freeze > requirements.txt

# Format code (if black is installed)
pip install black
black main.py

# Run linting (if flake8 is installed)
pip install flake8
flake8 main.py
```

## Architecture

The application follows a simple procedural design in a single file (`main.py`):

1. **Configuration Loading**: Environment variables are loaded from `.env` file containing API keys and location coordinates
2. **Weather API Integration**: Makes HTTP requests to OpenWeatherMap API to fetch 5-day forecast data
3. **Data Processing**: Filters forecasts for rain events in the next 48 hours and maps weather codes to emoji
4. **Telegram Notification**: Sends formatted messages to specified chat when rain is detected

### Key Components

- **Weather Icon Mapping** (main.py:22-32): Converts OpenWeatherMap icon codes to emoji for better visualization
- **Time Filtering Logic** (main.py:37-42): Only processes forecasts for today and tomorrow
- **Message Formatting** (main.py:60-75): Creates Markdown-formatted messages with date headers and time-based rain predictions
- **API Integration**: Direct HTTP requests without abstraction layers

### Data Flow

1. Load configuration from `.env`
2. Request 5-day forecast from OpenWeatherMap API
3. Filter forecast items for next 48 hours
4. Extract rain events with weather descriptions
5. Format message with dates, times, and weather emoji
6. Send to Telegram if rain is detected

### External Dependencies

- `requests`: HTTP client for API calls
- `python-dotenv`: Environment variable management
- OpenWeatherMap API: Weather data source (5 day/3 hour forecast endpoint)
- Telegram Bot API: Notification delivery (sendMessage endpoint)

## Environment Configuration

Required environment variables in `.env`:
- `OPENWEATHER_API_KEY`: API key from OpenWeatherMap
- `TELEGRAM_TOKEN`: Bot token from BotFather
- `CHAT_ID`: Target Telegram chat/channel ID
- `LAT`, `LON`: Geographic coordinates for weather location

## Code Patterns and Conventions

- **No Error Handling**: The script assumes API calls succeed
- **Inline Constants**: Weather icon mappings are hardcoded in the main flow
- **Single Execution**: Designed for periodic external scheduling (cron)
- **Console Output**: Uses print statements for execution feedback
- **Time Handling**: Uses UTC timestamps from API, formats to local display

## Deployment Notes

This bot is designed to run periodically (e.g., via cron job) with two different modes:

### Daily Report Mode (--mode daily)
Checks weather for today and tomorrow. Run this once daily at 12:01 AM:
```bash
# Daily report at 12:01 AM
1 0 * * * cd /path/to/cek_cuaca_bot && /path/to/.venv/bin/python main.py --mode daily
```

### 30-Minute Alert Mode (--mode alert)
Checks for rain in the next 30 minutes. Run this every 30 minutes:
```bash
# 30-minute alerts every 30 minutes
*/30 * * * * cd /path/to/cek_cuaca_bot && /path/to/.venv/bin/python main.py --mode alert
```

### Complete Cron Setup
Add both entries to your crontab for full functionality:
```bash
# Edit crontab
crontab -e

# Add these lines:
1 0 * * * cd /path/to/cek_cuaca_bot && /path/to/.venv/bin/python main.py --mode daily
*/30 * * * * cd /path/to/cek_cuaca_bot && /path/to/.venv/bin/python main.py --mode alert
```

The bot does not include built-in scheduling and relies on external schedulers for periodic execution.

## Potential Improvements

When extending this bot, consider:
- Adding error handling for API failures
- Implementing retry logic for network issues
- Adding logging instead of print statements
- Supporting multiple locations
- Creating a dry-run mode
- Adding unit tests for data processing logic
- Extracting configuration to a separate module