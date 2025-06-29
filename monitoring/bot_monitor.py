"""
Bot process monitoring module.
Ensures that the bot processes for Xenorize and Cryptellar are running properly.
"""
import logging
import requests
import psutil
import subprocess
import os
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("monitoring.bot_monitor")

# Track previous restart attempts to avoid excessive restarts
restart_attempts = {
    "xenorize_bot": {
        "count": 0,
        "last_attempt": 0
    },
    "cryptellar_bot": {
        "count": 0,
        "last_attempt": 0
    }
}

# Maximum restart attempts in a 24-hour period
MAX_RESTART_ATTEMPTS = 3
# Cooldown period in seconds (24 hours)
RESTART_COOLDOWN = 86400


class BotProcessMonitor:
    """
    Monitor and control bot processes for Xenorize and Cryptellar.
    Can detect if processes are running and attempt to restart them if necessary.
    """
    
    def __init__(self, service_name: str, config: Any):
        """
        Initialize the bot process monitor.
        
        Args:
            service_name: Name of the bot service (xenorize_bot or cryptellar_bot)
            config: Application configuration
        """
        self.service_name = service_name
        self.config = config
        
        # Set the appropriate API URL and key based on service name
        if service_name == "xenorize_bot":
            self.api_url = config.xenorize_api_url
            self.api_key = config.xenorize_api_key
            self.process_name = config.xenorize_bot_process
            self.start_command = config.xenorize_bot_start_command
            self.start_directory = config.xenorize_bot_directory
        else:  # cryptellar_bot
            self.api_url = config.cryptellar_api_url
            self.api_key = config.cryptellar_api_key
            self.process_name = config.cryptellar_bot_process
            self.start_command = config.cryptellar_bot_start_command
            self.start_directory = config.cryptellar_bot_directory
    
    def check_process_running(self) -> Dict[str, Any]:
        """
        Check if the bot process is running.
        
        Returns:
            Dictionary with process status information
        """
        try:
            running_processes = []
            
            # Search for processes by name
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    # Check if the process name or command line contains the bot process name
                    if (self.process_name in proc_info['name'] or 
                        (proc_info['cmdline'] and any(self.process_name in cmd for cmd in proc_info['cmdline']))):
                        running_processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if running_processes:
                return {
                    "status": "ok",
                    "running": True,
                    "process_count": len(running_processes),
                    "processes": running_processes,
                    "service": self.service_name
                }
            else:
                return {
                    "status": "error",
                    "running": False,
                    "error": f"Bot process '{self.process_name}' not found",
                    "service": self.service_name
                }
        except Exception as e:
            return {
                "status": "error",
                "running": False,
                "error": str(e),
                "service": self.service_name
            }
    
    def check_bot_api_status(self) -> Dict[str, Any]:
        """
        Check if the bot is responding via its API.
        
        Returns:
            Dictionary with bot API status information
        """
        try:
            # Use bot status endpoint
            url = f"{self.api_url}/bot/status"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "ok" if data.get("is_running", False) else "error",
                    "running": data.get("is_running", False),
                    "details": data,
                    "service": self.service_name
                }
            else:
                return {
                    "status": "error",
                    "running": False,
                    "error": f"Bot API returned status code {response.status_code}",
                    "service": self.service_name
                }
        except requests.exceptions.Timeout:
            return {
                "status": "error", 
                "running": False,
                "error": "Request timed out", 
                "service": self.service_name
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error", 
                "running": False,
                "error": "Connection failed", 
                "service": self.service_name
            }
        except Exception as e:
            return {
                "status": "error", 
                "running": False,
                "error": str(e), 
                "service": self.service_name
            }
    
    def attempt_restart(self) -> Dict[str, Any]:
        """
        Attempt to restart the bot process if it's down.
        
        Returns:
            Dictionary with restart attempt information
        """
        global restart_attempts
        
        # Check if we've exceeded the maximum restart attempts
        current_time = time.time()
        if (restart_attempts[self.service_name]["count"] >= MAX_RESTART_ATTEMPTS and 
            current_time - restart_attempts[self.service_name]["last_attempt"] < RESTART_COOLDOWN):
            return {
                "status": "error",
                "error": f"Maximum restart attempts ({MAX_RESTART_ATTEMPTS}) exceeded in 24-hour period",
                "service": self.service_name
            }
        
        try:
            logger.info(f"Attempting to restart {self.service_name}")
            
            # Update restart attempts counter
            restart_attempts[self.service_name]["count"] += 1
            restart_attempts[self.service_name]["last_attempt"] = current_time
            
            # Execute the restart command
            result = subprocess.run(
                self.start_command,
                shell=True,
                cwd=self.start_directory,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "status": "ok",
                    "message": f"Successfully restarted {self.service_name}",
                    "output": result.stdout,
                    "service": self.service_name
                }
            else:
                return {
                    "status": "error",
                    "error": f"Failed to restart {self.service_name}",
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                    "service": self.service_name
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": self.service_name
            }


def run_bot_monitoring(config, notifier) -> None:
    """
    Check the status of bot processes and attempt to restart them if necessary.
    
    Args:
        config: Application configuration
        notifier: Notification service
    """
    logger.info("Running bot process checks")
    
    # Check Xenorize bot if configured
    if hasattr(config, 'xenorize_bot_process') and config.xenorize_bot_process:
        monitor = BotProcessMonitor("xenorize_bot", config)
        
        # Check if process is running
        process_status = monitor.check_process_running()
        api_status = monitor.check_bot_api_status()
        
        process_running = process_status.get("running", False)
        api_running = api_status.get("running", False)
        
        # Alert if either the process or API is down
        if not process_running or not api_running:
            issue_description = []
            
            if not process_running:
                issue_description.append(f"Process not running: {process_status.get('error', 'Unknown error')}")
            
            if not api_running:
                issue_description.append(f"API not responding: {api_status.get('error', 'Unknown error')}")
            
            logger.warning(f"Xenorize bot issues detected: {', '.join(issue_description)}")
            
            # Send notification
            notifier.send_alert(
                f"🚨 BOT DOWN: XENORIZE\n\n"
                f"Issues:\n- {'\n- '.join(issue_description)}\n\n"
                f"Attempting automatic restart..."
            )
            
            # Attempt restart
            restart_result = monitor.attempt_restart()
            
            if restart_result["status"] == "ok":
                notifier.send_alert(
                    f"✅ RESTART SUCCESSFUL: XENORIZE\n\n"
                    f"The bot has been restarted automatically."
                )
                logger.info("Xenorize bot restarted successfully")
            else:
                notifier.send_alert(
                    f"❌ RESTART FAILED: XENORIZE\n\n"
                    f"Error: {restart_result.get('error', 'Unknown error')}\n\n"
                    f"Manual intervention required!"
                )
                logger.error(f"Failed to restart Xenorize bot: {restart_result.get('error', 'Unknown error')}")
    
    # Check Cryptellar bot if configured
    if hasattr(config, 'cryptellar_bot_process') and config.cryptellar_bot_process:
        monitor = BotProcessMonitor("cryptellar_bot", config)
        
        # Check if process is running
        process_status = monitor.check_process_running()
        api_status = monitor.check_bot_api_status()
        
        process_running = process_status.get("running", False)
        api_running = api_status.get("running", False)
        
        # Alert if either the process or API is down
        if not process_running or not api_running:
            issue_description = []
            
            if not process_running:
                issue_description.append(f"Process not running: {process_status.get('error', 'Unknown error')}")
            
            if not api_running:
                issue_description.append(f"API not responding: {api_status.get('error', 'Unknown error')}")
            
            logger.warning(f"Cryptellar bot issues detected: {', '.join(issue_description)}")
            
            # Send notification
            notifier.send_alert(
                f"🚨 BOT DOWN: CRYPTELLAR\n\n"
                f"Issues:\n- {'\n- '.join(issue_description)}\n\n"
                f"Attempting automatic restart..."
            )
            
            # Attempt restart
            restart_result = monitor.attempt_restart()
            
            if restart_result["status"] == "ok":
                notifier.send_alert(
                    f"✅ RESTART SUCCESSFUL: CRYPTELLAR\n\n"
                    f"The bot has been restarted automatically."
                )
                logger.info("Cryptellar bot restarted successfully")
            else:
                notifier.send_alert(
                    f"❌ RESTART FAILED: CRYPTELLAR\n\n"
                    f"Error: {restart_result.get('error', 'Unknown error')}\n\n"
                    f"Manual intervention required!"
                )
                logger.error(f"Failed to restart Cryptellar bot: {restart_result.get('error', 'Unknown error')}")
