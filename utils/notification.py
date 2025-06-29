"""
Notification module for the monitoring system.
Provides functionality to send alerts via Telegram.
"""
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("utils.notification")


class TelegramNotifier:
    """
    Telegram notification service for sending alerts.
    """
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize the Telegram notifier.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Check if configuration is valid
        self.is_configured = bool(bot_token and chat_id)
        
        if not self.is_configured:
            logger.warning("Telegram notification is not properly configured")
    
    def send_alert(self, message: str) -> bool:
        """
        Send an alert message to Telegram.
        
        Args:
            message: The alert message to send
            
        Returns:
            True if the message was sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning("Cannot send Telegram alert: notifier not configured")
            return False
            
        # Add timestamp to the message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}]\n{message}"
        
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': full_message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(self.api_url, data=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram notification sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {str(e)}")
            return False
