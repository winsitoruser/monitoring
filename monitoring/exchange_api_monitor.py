"""
Exchange API monitoring module.
Provides monitoring for cryptocurrency exchange APIs, webhooks and connection status.
"""

import logging
import requests
import json
import time
import os
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("monitoring.exchange_api")

class ExchangeAPIMonitor:
    """
    Monitor cryptocurrency exchange APIs, webhooks and connection health.
    """
    
    def __init__(self, config: Any, notifier=None):
        """
        Initialize the exchange API monitor.
        
        Args:
            config: Application configuration
            notifier: Optional notification service
        """
        self.config = config
        self.notifier = notifier
        self.exchanges = self._load_exchanges()
        self.webhooks = self._load_webhooks()
        self.last_check_time = {}
        self.response_times = {}
        self.rate_limit_info = {}
        self.connectivity_status = {}
        self.webhook_status = {}
        
        # Ensure data directory exists
        os.makedirs("data/exchange_api", exist_ok=True)
    
    def _load_exchanges(self) -> Dict[str, Dict[str, Any]]:
        """
        Load exchange configurations from environment variables.
        
        Returns:
            Dictionary of exchange configurations
        """
        exchanges = {}
        
        # Load from config
        exchange_list = getattr(self.config, "monitored_exchanges", [])
        
        for exchange_name in exchange_list:
            exchange_conf = {}
            exchange_conf["name"] = exchange_name
            
            # Get API credentials from config
            api_key_var = f"{exchange_name.upper()}_API_KEY"
            api_secret_var = f"{exchange_name.upper()}_API_SECRET"
            api_base_url_var = f"{exchange_name.upper()}_API_URL"
            
            exchange_conf["api_key"] = getattr(self.config, exchange_name.lower() + "_api_key", "")
            exchange_conf["api_secret"] = getattr(self.config, exchange_name.lower() + "_api_secret", "")
            exchange_conf["base_url"] = getattr(self.config, exchange_name.lower() + "_api_url", "")
            
            # Endpoints to check for this exchange
            endpoints_var = f"{exchange_name.upper()}_ENDPOINTS"
            endpoints_str = getattr(self.config, exchange_name.lower() + "_endpoints", "")
            
            if endpoints_str:
                exchange_conf["endpoints"] = [ep.strip() for ep in endpoints_str.split(",")]
            else:
                # Default endpoints to check
                if exchange_name.lower() == "binance":
                    exchange_conf["endpoints"] = ["/api/v3/ping", "/api/v3/time", "/api/v3/exchangeInfo"]
                elif exchange_name.lower() == "coinbase":
                    exchange_conf["endpoints"] = ["/currencies", "/time"]
                elif exchange_name.lower() == "kraken":
                    exchange_conf["endpoints"] = ["/0/public/Time", "/0/public/SystemStatus"]
                else:
                    exchange_conf["endpoints"] = ["/ping", "/status", "/time"]
            
            exchanges[exchange_name] = exchange_conf
            
        return exchanges
    
    def _load_webhooks(self) -> Dict[str, Dict[str, Any]]:
        """
        Load webhook configurations from environment variables.
        
        Returns:
            Dictionary of webhook configurations
        """
        webhooks = {}
        
        # Load from config
        webhook_list = getattr(self.config, "monitored_webhooks", [])
        
        for webhook_name in webhook_list:
            webhook_conf = {}
            webhook_conf["name"] = webhook_name
            
            # Get webhook details from config
            webhook_url_var = f"{webhook_name.upper()}_WEBHOOK_URL"
            webhook_secret_var = f"{webhook_name.upper()}_WEBHOOK_SECRET"
            webhook_test_payload_var = f"{webhook_name.upper()}_WEBHOOK_TEST_PAYLOAD"
            
            webhook_conf["url"] = getattr(self.config, webhook_name.lower() + "_webhook_url", "")
            webhook_conf["secret"] = getattr(self.config, webhook_name.lower() + "_webhook_secret", "")
            webhook_conf["test_payload"] = getattr(self.config, webhook_name.lower() + "_webhook_test_payload", "{}")
            
            # If no test payload provided, use a default one
            if webhook_conf["test_payload"] == "{}":
                webhook_conf["test_payload"] = json.dumps({
                    "event": "test",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"test": True}
                })
            
            webhooks[webhook_name] = webhook_conf
            
        return webhooks
            
    def check_exchange_api(self, exchange_name: str) -> Dict[str, Any]:
        """
        Check the health and status of a specific exchange API.
        
        Args:
            exchange_name: Name of the exchange to check
            
        Returns:
            Dictionary with exchange API status information
        """
        if exchange_name not in self.exchanges:
            logger.error(f"Exchange {exchange_name} not found in configuration")
            return {
                "exchange": exchange_name,
                "status": "error",
                "message": "Exchange not configured",
                "timestamp": datetime.now().isoformat()
            }
        
        exchange_config = self.exchanges[exchange_name]
        base_url = exchange_config["base_url"]
        endpoints = exchange_config["endpoints"]
        
        results = {
            "exchange": exchange_name,
            "status": "operational",
            "endpoints": {},
            "rate_limits": {},
            "response_times": {},
            "timestamp": datetime.now().isoformat()
        }
        
        has_error = False
        
        # Check each endpoint
        for endpoint in endpoints:
            start_time = time.time()
            try:
                url = f"{base_url.rstrip('/')}{endpoint}"
                logger.info(f"Checking API endpoint {url}")
                
                response = requests.get(url, timeout=10)
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                
                # Store response time
                results["response_times"][endpoint] = response_time
                if exchange_name not in self.response_times:
                    self.response_times[exchange_name] = {}
                self.response_times[exchange_name][endpoint] = response_time
                
                # Check rate limits from headers
                rate_limit_data = {}
                for header in response.headers:
                    if "rate" in header.lower() or "limit" in header.lower():
                        rate_limit_data[header] = response.headers[header]
                
                if rate_limit_data:
                    results["rate_limits"][endpoint] = rate_limit_data
                    if exchange_name not in self.rate_limit_info:
                        self.rate_limit_info[exchange_name] = {}
                    self.rate_limit_info[exchange_name][endpoint] = rate_limit_data
                
                # Check response status
                if response.status_code == 200:
                    endpoint_status = "ok"
                    try:
                        # Try to parse JSON response
                        data = response.json()
                        results["endpoints"][endpoint] = {
                            "status": endpoint_status,
                            "status_code": response.status_code,
                            "response_time": response_time,
                            "data": data
                        }
                    except ValueError:
                        # Not JSON response
                        results["endpoints"][endpoint] = {
                            "status": endpoint_status,
                            "status_code": response.status_code,
                            "response_time": response_time,
                            "data": response.text[:100] + "..."  # Truncate long responses
                        }
                else:
                    endpoint_status = "error"
                    has_error = True
                    results["endpoints"][endpoint] = {
                        "status": endpoint_status,
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "error": response.text[:100] + "..."  # Truncate long error messages
                    }
            
            except requests.exceptions.Timeout:
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                has_error = True
                results["endpoints"][endpoint] = {
                    "status": "timeout",
                    "response_time": response_time,
                    "error": "Request timed out"
                }
                
            except requests.exceptions.RequestException as e:
                has_error = True
                results["endpoints"][endpoint] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Update overall status
        if has_error:
            results["status"] = "degraded"
        
        # Store last check time
        self.last_check_time[exchange_name] = datetime.now()
        
        # Store connectivity status
        self.connectivity_status[exchange_name] = results["status"]
        
        # Save results to file
        try:
            with open(f"data/exchange_api/{exchange_name}_status.json", "w") as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {exchange_name} status to file: {e}")
        
        # Send notification if status is degraded and notifier is available
        if has_error and self.notifier:
            error_endpoints = [
                f"{ep}: {results['endpoints'][ep]['status']} ({results['endpoints'][ep].get('status_code', 'N/A')})" 
                for ep in results["endpoints"] 
                if results["endpoints"][ep]["status"] != "ok"
            ]
            
            self.notifier.send_alert(
                f"⚠️ EXCHANGE API ALERT: {exchange_name.upper()}\n\n"
                f"Status: {results['status']}\n\n"
                f"Problem endpoints:\n- " + "\n- ".join(error_endpoints) + "\n\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        return results
    
    def test_webhook(self, webhook_name: str) -> Dict[str, Any]:
        """
        Test a webhook by sending a test payload.
        
        Args:
            webhook_name: Name of the webhook to test
            
        Returns:
            Dictionary with webhook test results
        """
        if webhook_name not in self.webhooks:
            logger.error(f"Webhook {webhook_name} not found in configuration")
            return {
                "webhook": webhook_name,
                "status": "error",
                "message": "Webhook not configured",
                "timestamp": datetime.now().isoformat()
            }
        
        webhook_config = self.webhooks[webhook_name]
        url = webhook_config["url"]
        secret = webhook_config["secret"]
        payload = webhook_config["test_payload"]
        
        try:
            # Prepare payload
            if isinstance(payload, str):
                payload_data = json.loads(payload)
            else:
                payload_data = payload
                
            # Add timestamp if not present
            if "timestamp" not in payload_data:
                payload_data["timestamp"] = datetime.now().isoformat()
            
            # Convert to JSON string
            payload_str = json.dumps(payload_data)
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add signature if secret is provided
            if secret:
                signature = hmac.new(
                    secret.encode("utf-8"),
                    payload_str.encode("utf-8"),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Signature"] = signature
            
            # Send test webhook
            start_time = time.time()
            response = requests.post(url, data=payload_str, headers=headers, timeout=10)
            end_time = time.time()
            response_time = round(end_time - start_time, 2)
            
            # Check response
            if response.status_code >= 200 and response.status_code < 300:
                status = "delivered"
                message = f"Webhook delivered successfully (status {response.status_code})"
            else:
                status = "failed"
                message = f"Webhook delivery failed (status {response.status_code}): {response.text[:100]}"
            
            result = {
                "webhook": webhook_name,
                "status": status,
                "message": message,
                "response_code": response.status_code,
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store webhook status
            self.webhook_status[webhook_name] = status
            
            # Save results to file
            try:
                with open(f"data/exchange_api/{webhook_name}_webhook.json", "w") as f:
                    json.dump(result, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save {webhook_name} webhook status to file: {e}")
            
            # Send notification if delivery failed and notifier is available
            if status == "failed" and self.notifier:
                self.notifier.send_alert(
                    f"⚠️ WEBHOOK DELIVERY ALERT: {webhook_name.upper()}\n\n"
                    f"Status: {status}\n"
                    f"Message: {message}\n\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            return result
            
        except Exception as e:
            error_result = {
                "webhook": webhook_name,
                "status": "error",
                "message": f"Error testing webhook: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            
            # Store webhook status
            self.webhook_status[webhook_name] = "error"
            
            # Send notification if notifier is available
            if self.notifier:
                self.notifier.send_alert(
                    f"⚠️ WEBHOOK TEST ERROR: {webhook_name.upper()}\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            return error_result
    
    def get_exchange_status_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all exchange API statuses.
        
        Returns:
            Dictionary with status summary for all exchanges
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "exchanges": {},
            "overall_status": "operational"
        }
        
        for exchange_name in self.exchanges:
            if exchange_name in self.connectivity_status:
                exchange_status = self.connectivity_status[exchange_name]
                last_check = self.last_check_time.get(exchange_name, "Never")
                
                if isinstance(last_check, datetime):
                    last_check = last_check.isoformat()
                
                summary["exchanges"][exchange_name] = {
                    "status": exchange_status,
                    "last_check": last_check
                }
                
                # Add response time information if available
                if exchange_name in self.response_times:
                    avg_response_time = sum(self.response_times[exchange_name].values()) / len(self.response_times[exchange_name])
                    summary["exchanges"][exchange_name]["avg_response_time"] = round(avg_response_time, 2)
                
                # Update overall status to worst status
                if exchange_status == "degraded" and summary["overall_status"] == "operational":
                    summary["overall_status"] = "degraded"
            else:
                summary["exchanges"][exchange_name] = {
                    "status": "unknown",
                    "last_check": "Never"
                }
        
        return summary
    
    def get_webhook_status_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all webhook statuses.
        
        Returns:
            Dictionary with status summary for all webhooks
        """
        summary = {
            "timestamp": datetime.now().isoformat(),
            "webhooks": {},
            "overall_status": "operational"
        }
        
        for webhook_name in self.webhooks:
            if webhook_name in self.webhook_status:
                webhook_status = self.webhook_status[webhook_name]
                
                summary["webhooks"][webhook_name] = {
                    "status": webhook_status
                }
                
                # Update overall status
                if webhook_status != "delivered" and summary["overall_status"] == "operational":
                    summary["overall_status"] = "degraded"
            else:
                summary["webhooks"][webhook_name] = {
                    "status": "unknown"
                }
        
        return summary


def run_exchange_api_checks(config, notifier=None) -> None:
    """
    Run checks for all configured exchange APIs.
    
    Args:
        config: Application configuration
        notifier: Optional notification service
    """
    logger.info("Running exchange API checks")
    
    # Initialize monitor
    monitor = ExchangeAPIMonitor(config, notifier)
    
    # Check each exchange
    for exchange_name in monitor.exchanges:
        try:
            logger.info(f"Checking exchange API: {exchange_name}")
            monitor.check_exchange_api(exchange_name)
        except Exception as e:
            logger.error(f"Error checking exchange {exchange_name}: {e}")
    
    # Get status summary and save to file
    summary = monitor.get_exchange_status_summary()
    try:
        with open("data/exchange_api_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save exchange API summary to file: {e}")
    
    return summary


def test_webhooks(config, notifier=None) -> None:
    """
    Test all configured webhooks.
    
    Args:
        config: Application configuration
        notifier: Optional notification service
    """
    logger.info("Testing webhooks")
    
    # Initialize monitor
    monitor = ExchangeAPIMonitor(config, notifier)
    
    # Test each webhook
    for webhook_name in monitor.webhooks:
        try:
            logger.info(f"Testing webhook: {webhook_name}")
            monitor.test_webhook(webhook_name)
        except Exception as e:
            logger.error(f"Error testing webhook {webhook_name}: {e}")
    
    # Get webhook status summary and save to file
    summary = monitor.get_webhook_status_summary()
    try:
        with open("data/webhook_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save webhook summary to file: {e}")
    
    return summary
