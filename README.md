# Monitoring System for Xenorize and Cryptellar

A comprehensive monitoring system that provides health checks, custom exception tracking, API connection monitoring, performance tracking, and Telegram notifications for the Xenorize and Cryptellar bot platforms.

## Features

- **Health Checks**: Monitors API endpoints, bot functionality, and service availability
- **Custom Exception Tracking**: Captures and reports exceptions in your applications
- **Performance Monitoring**: Tracks CPU, memory, and disk usage
- **Telegram Notifications**: Sends alerts when issues are detected
- **Simple Configuration**: Easy setup via environment variables
- **Exchange Monitoring**: Monitors cryptocurrency exchange API endpoints and webhooks

## Setup

1. Clone this repository
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Copy `.env.example` to `.env` and configure your environment variables:
```
cp .env.example .env
nano .env  # Edit with your values
```

## Configuration

Edit the `.env` file with your specific settings:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token for notifications
- `TELEGRAM_CHAT_ID`: Chat ID where notifications should be sent
- `CHECK_INTERVAL`: How often to run health checks (in seconds)
- `ALERT_THRESHOLD`: Number of consecutive failures before alerting
- `XENORIZE_API_URL` and `XENORIZE_API_KEY`: API details for Xenorize
- `CRYPTELLAR_API_URL` and `CRYPTELLAR_API_KEY`: API details for Cryptellar

## Running the Application

```
python main.py
```

The monitoring service will start and begin checking the health of your services at the configured interval.

## Integrating with Your Bot Projects

### Exception Tracking

Add the exception tracking decorator to functions you want to monitor:

```python
from monitoring.exception_tracker import exception_handler

@exception_handler
def your_function():
    # Your code here
```

### Custom Metrics

To add custom metrics to your monitoring, extend the health check module.

## Logs

Logs are stored in `monitoring.log` in the root directory.
