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

# Run the bot
python main.py
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
- **Time Filtering Logic**: Only processes forecasts for today and tomorrow
- **Message Formatting**: Creates Markdown-formatted messages with date headers and time-based rain predictions

### External Dependencies

- `requests`: HTTP client for API calls
- `python-dotenv`: Environment variable management
- OpenWeatherMap API: Weather data source
- Telegram Bot API: Notification delivery

## Environment Configuration

Required environment variables in `.env`:
- `OPENWEATHER_API_KEY`: API key from OpenWeatherMap
- `TELEGRAM_TOKEN`: Bot token from BotFather
- `CHAT_ID`: Target Telegram chat/channel ID
- `LAT`, `LON`: Geographic coordinates for weather location

## Deployment Notes

This bot is designed to run periodically (e.g., via cron job). A typical cron entry might be:
```bash
0 6 * * * cd /path/to/cek_cuaca_bot && /path/to/.venv/bin/python main.py
```

The bot does not include built-in scheduling and relies on external schedulers for periodic execution.