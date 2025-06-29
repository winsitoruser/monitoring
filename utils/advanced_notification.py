"""
Advanced notification system.
Provides multi-channel notifications via Telegram, Slack, Email, SMS, and more.
"""

import logging
import requests
import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

logger = logging.getLogger("utils.advanced_notification")

class BaseNotifier:
    """Base class for notification channels."""
    
    def __init__(self, config):
        self.config = config
        self.notification_history = []
    
    def send_message(self, message: str, subject: str = None, priority: str = "normal") -> bool:
        """
        Send a message through this channel.
        
        Args:
            message: Message content to send
            subject: Optional subject line
            priority: Priority level (low, normal, high, critical)
        
        Returns:
            Boolean indicating success
        """
        raise NotImplementedError("Subclasses must implement send_message")
    
    def log_notification(self, message: str, subject: str, priority: str, success: bool):
        """
        Log a notification to history.
        
        Args:
            message: Message content
            subject: Subject line
            priority: Priority level
            success: Whether the notification was sent successfully
        """
        self.notification_history.append({
            "timestamp": datetime.now().isoformat(),
            "message": message[:100] + "..." if len(message) > 100 else message,
            "subject": subject,
            "priority": priority,
            "success": success
        })
        
        # Keep history to a reasonable size
        if len(self.notification_history) > 100:
            self.notification_history = self.notification_history[-100:]


class TelegramAdvancedNotifier(BaseNotifier):
    """Send notifications via Telegram."""
    
    def __init__(self, config):
        super().__init__(config)
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.enabled = bool(self.bot_token and self.chat_id)
    
    def send_message(self, message: str, subject: str = None, priority: str = "normal") -> bool:
        """
        Send a message via Telegram.
        
        Args:
            message: Message content to send
            subject: Optional subject line
            priority: Priority level (low, normal, high, critical)
        
        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            logger.warning("Telegram notifications are not configured")
            self.log_notification(message, subject, priority, False)
            return False
        
        # Add emoji based on priority
        priority_emoji = {
            "low": "ℹ️",
            "normal": "🔔",
            "high": "⚠️",
            "critical": "🚨"
        }
        
        emoji = priority_emoji.get(priority.lower(), "🔔")
        
        # Format message with subject
        formatted_message = f"{emoji} "
        if subject:
            formatted_message += f"*{subject}*\n\n"
        formatted_message += message
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Telegram notification sent: {subject}")
                self.log_notification(message, subject, priority, True)
                return True
            else:
                logger.error(f"Failed to send Telegram notification: {response.text}")
                self.log_notification(message, subject, priority, False)
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            self.log_notification(message, subject, priority, False)
            return False


class SlackNotifier(BaseNotifier):
    """Send notifications via Slack."""
    
    def __init__(self, config):
        super().__init__(config)
        self.webhook_url = config.slack_webhook_url
        self.channel = getattr(config, "slack_channel", "#alerts")
        self.username = getattr(config, "slack_username", "Monitoring Bot")
        self.enabled = bool(self.webhook_url)
    
    def send_message(self, message: str, subject: str = None, priority: str = "normal") -> bool:
        """
        Send a message via Slack.
        
        Args:
            message: Message content to send
            subject: Optional subject line
            priority: Priority level (low, normal, high, critical)
        
        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            logger.warning("Slack notifications are not configured")
            self.log_notification(message, subject, priority, False)
            return False
        
        # Map priority to color
        priority_color = {
            "low": "#36a64f",  # green
            "normal": "#2196f3",  # blue
            "high": "#ffc107",  # yellow
            "critical": "#f44336"  # red
        }
        
        color = priority_color.get(priority.lower(), "#2196f3")
        
        # Build payload
        payload = {
            "channel": self.channel,
            "username": self.username,
            "attachments": [
                {
                    "color": color,
                    "title": subject if subject else "Monitoring Alert",
                    "text": message,
                    "footer": f"Priority: {priority.upper()} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        }
        
        try:
            response = requests.post(
                self.webhook_url, 
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Slack notification sent: {subject}")
                self.log_notification(message, subject, priority, True)
                return True
            else:
                logger.error(f"Failed to send Slack notification: {response.text}")
                self.log_notification(message, subject, priority, False)
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            self.log_notification(message, subject, priority, False)
            return False


class EmailNotifier(BaseNotifier):
    """Send notifications via email."""
    
    def __init__(self, config):
        super().__init__(config)
        self.smtp_server = config.email_smtp_server
        self.smtp_port = config.email_smtp_port
        self.smtp_username = config.email_smtp_username
        self.smtp_password = config.email_smtp_password
        self.from_email = config.email_from
        self.to_emails = config.email_recipients
        self.enabled = bool(self.smtp_server and self.smtp_username and self.smtp_password and self.to_emails)
    
    def send_message(self, message: str, subject: str = None, priority: str = "normal") -> bool:
        """
        Send a message via email.
        
        Args:
            message: Message content to send
            subject: Optional subject line
            priority: Priority level (low, normal, high, critical)
        
        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            logger.warning("Email notifications are not configured")
            self.log_notification(message, subject, priority, False)
            return False
        
        # If no subject is provided, create one based on priority
        if not subject:
            subject = f"Monitoring Alert - {priority.upper()}"
        else:
            # Add priority to subject
            subject = f"[{priority.upper()}] {subject}"
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_emails) if isinstance(self.to_emails, list) else self.to_emails
        
        # Add plain text and HTML parts
        text_part = MIMEText(message, "plain")
        html_message = message.replace("\n", "<br>")
        html_part = MIMEText(f"<html><body><p>{html_message}</p></body></html>", "html")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            server.sendmail(
                self.from_email,
                self.to_emails if isinstance(self.to_emails, list) else [self.to_emails],
                msg.as_string()
            )
            server.quit()
            
            logger.info(f"Email notification sent: {subject}")
            self.log_notification(message, subject, priority, True)
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            self.log_notification(message, subject, priority, False)
            return False


class SMSNotifier(BaseNotifier):
    """Send notifications via SMS using Twilio."""
    
    def __init__(self, config):
        super().__init__(config)
        self.account_sid = config.twilio_account_sid
        self.auth_token = config.twilio_auth_token
        self.from_number = config.twilio_from_number
        self.to_numbers = config.twilio_to_numbers
        self.enabled = bool(self.account_sid and self.auth_token and self.from_number and self.to_numbers)
    
    def send_message(self, message: str, subject: str = None, priority: str = "normal") -> bool:
        """
        Send a message via SMS.
        
        Args:
            message: Message content to send
            subject: Optional subject line
            priority: Priority level (low, normal, high, critical)
        
        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            logger.warning("SMS notifications are not configured")
            self.log_notification(message, subject, priority, False)
            return False
        
        # Only send SMS for high and critical priority
        if priority.lower() not in ["high", "critical"]:
            logger.info(f"Skipping SMS notification for {priority} priority")
            return True
        
        # Format message
        sms_message = message
        if subject:
            sms_message = f"{subject}: {message}"
        
        # Truncate to 160 characters for SMS
        if len(sms_message) > 157:
            sms_message = sms_message[:157] + "..."
        
        try:
            # Import here to avoid requiring twilio if not used
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            
            # If to_numbers is a string, convert to list
            to_numbers = self.to_numbers
            if isinstance(to_numbers, str):
                to_numbers = [number.strip() for number in to_numbers.split(",")]
            
            success = True
            
            # Send to each number
            for number in to_numbers:
                message = client.messages.create(
                    body=sms_message,
                    from_=self.from_number,
                    to=number
                )
                
                if not message.sid:
                    success = False
                    logger.error(f"Failed to send SMS to {number}")
            
            if success:
                logger.info(f"SMS notification(s) sent: {subject}")
                self.log_notification(message, subject, priority, True)
                return True
            else:
                logger.error("Some SMS notifications failed to send")
                self.log_notification(message, subject, priority, False)
                return False
                
        except ImportError:
            logger.error("Twilio library not installed. Cannot send SMS.")
            self.log_notification(message, subject, priority, False)
            return False
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            self.log_notification(message, subject, priority, False)
            return False


class NotificationManager:
    """
    Manage multiple notification channels and provide unified interface.
    """
    
    def __init__(self, config):
        """
        Initialize the notification manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.channels = {}
        
        # Initialize channels based on configuration
        if getattr(config, "enable_telegram_notifications", True):
            self.channels["telegram"] = TelegramAdvancedNotifier(config)
        
        if getattr(config, "enable_slack_notifications", False):
            self.channels["slack"] = SlackNotifier(config)
        
        if getattr(config, "enable_email_notifications", False):
            self.channels["email"] = EmailNotifier(config)
        
        if getattr(config, "enable_sms_notifications", False):
            self.channels["sms"] = SMSNotifier(config)
    
    def send_alert(self, message: str, subject: str = None, priority: str = "normal",
                   channels: List[str] = None) -> Dict[str, bool]:
        """
        Send an alert through configured channels.
        
        Args:
            message: Alert message
            subject: Optional subject line
            priority: Priority level (low, normal, high, critical)
            channels: Specific channels to use (if None, use all)
            
        Returns:
            Dictionary with channel names and success status
        """
        results = {}
        
        # If no channels specified, use all available channels
        if not channels:
            target_channels = self.channels.keys()
        else:
            target_channels = [ch for ch in channels if ch in self.channels]
        
        # Send to each channel
        for channel_name in target_channels:
            channel = self.channels[channel_name]
            try:
                results[channel_name] = channel.send_message(message, subject, priority)
            except Exception as e:
                logger.error(f"Error sending through {channel_name}: {e}")
                results[channel_name] = False
        
        # For high and critical alerts, ensure at least one channel worked
        if priority.lower() in ["high", "critical"] and not any(results.values()):
            logger.critical(f"Failed to send {priority} alert through any channel: {message}")
        
        return results
    
    def get_notification_history(self, channel: str = None) -> List[Dict[str, Any]]:
        """
        Get notification history for a channel or all channels.
        
        Args:
            channel: Optional channel name to filter by
            
        Returns:
            List of notification history entries
        """
        if channel and channel in self.channels:
            return self.channels[channel].notification_history
        
        # Combine all histories
        combined_history = []
        for channel_name, channel_obj in self.channels.items():
            for entry in channel_obj.notification_history:
                entry["channel"] = channel_name
                combined_history.append(entry)
        
        # Sort by timestamp, newest first
        return sorted(combined_history, key=lambda x: x["timestamp"], reverse=True)
