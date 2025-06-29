"""
Uptime monitoring module.
Integrates with external uptime monitoring services like Pingdom, UptimeRobot, and StatusCake.
Also provides an internal uptime monitoring implementation.
"""
import logging
import time
import json
import os
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("monitoring.uptime_monitor")

# Dictionary to store uptime history
# Format: {endpoint: [(timestamp, status_code, response_time), ...]}
uptime_history = {}

# Maximum history entries per endpoint
MAX_HISTORY_ENTRIES = 1000


class UptimeMonitor:
    """Base class for uptime monitoring."""
    
    def __init__(self, config: Any):
        """
        Initialize uptime monitoring.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.endpoints = []
    
    def register_endpoints(self, endpoints: List[Dict[str, Any]]) -> None:
        """
        Register endpoints to monitor.
        
        Args:
            endpoints: List of endpoint configurations
                Each endpoint should be a dictionary with:
                - url: The URL to monitor
                - name: A friendly name for the endpoint
                - timeout: Request timeout in seconds (optional)
                - expected_status: Expected HTTP status code (optional, default 200)
                - check_string: String that should be present in the response (optional)
                - headers: Dictionary of headers to include in the request (optional)
        """
        self.endpoints = endpoints
    
    def check_uptime(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if an endpoint is up.
        
        Args:
            endpoint: Endpoint configuration dictionary
            
        Returns:
            Dictionary with uptime check results
        """
        url = endpoint['url']
        name = endpoint.get('name', url)
        timeout = endpoint.get('timeout', 10)
        expected_status = endpoint.get('expected_status', 200)
        check_string = endpoint.get('check_string', None)
        headers = endpoint.get('headers', {})
        
        start_time = time.time()
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response_time = time.time() - start_time
            
            # Check if status code matches expected
            status_match = response.status_code == expected_status
            
            # Check if expected string is in response if specified
            content_match = True
            if check_string and check_string not in response.text:
                content_match = False
            
            is_up = status_match and content_match
            
            result = {
                'endpoint': name,
                'url': url,
                'is_up': is_up,
                'response_time': response_time,
                'status_code': response.status_code,
                'timestamp': datetime.utcnow().isoformat(),
                'expected_status': expected_status,
                'content_match': content_match
            }
            
            # Store in history
            if url not in uptime_history:
                uptime_history[url] = []
            
            uptime_history[url].append((
                datetime.utcnow(),
                response.status_code,
                response_time,
                is_up
            ))
            
            # Trim history if needed
            if len(uptime_history[url]) > MAX_HISTORY_ENTRIES:
                uptime_history[url] = uptime_history[url][-MAX_HISTORY_ENTRIES:]
            
            return result
        
        except requests.exceptions.Timeout:
            result = {
                'endpoint': name,
                'url': url,
                'is_up': False,
                'error': 'Timeout',
                'timestamp': datetime.utcnow().isoformat(),
                'response_time': time.time() - start_time
            }
            
            # Store in history
            if url not in uptime_history:
                uptime_history[url] = []
            
            uptime_history[url].append((
                datetime.utcnow(),
                0,  # 0 status code indicates error
                time.time() - start_time,
                False
            ))
            
            # Trim history if needed
            if len(uptime_history[url]) > MAX_HISTORY_ENTRIES:
                uptime_history[url] = uptime_history[url][-MAX_HISTORY_ENTRIES:]
                
            return result
        
        except Exception as e:
            result = {
                'endpoint': name,
                'url': url,
                'is_up': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'response_time': time.time() - start_time
            }
            
            # Store in history
            if url not in uptime_history:
                uptime_history[url] = []
            
            uptime_history[url].append((
                datetime.utcnow(),
                0,  # 0 status code indicates error
                time.time() - start_time,
                False
            ))
            
            # Trim history if needed
            if len(uptime_history[url]) > MAX_HISTORY_ENTRIES:
                uptime_history[url] = uptime_history[url][-MAX_HISTORY_ENTRIES:]
                
            return result
    
    def check_all_endpoints(self) -> List[Dict[str, Any]]:
        """
        Check all registered endpoints.
        
        Returns:
            List of uptime check results for each endpoint
        """
        results = []
        
        for endpoint in self.endpoints:
            try:
                result = self.check_uptime(endpoint)
                results.append(result)
            except Exception as e:
                logger.error(f"Error checking uptime for {endpoint.get('name', endpoint.get('url', 'unknown'))}: {e}")
                results.append({
                    'endpoint': endpoint.get('name', endpoint.get('url', 'unknown')),
                    'url': endpoint.get('url', ''),
                    'is_up': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        return results
    
    def get_uptime_history(self, url: str = None, hours: int = 24) -> Dict[str, Any]:
        """
        Get uptime history for specified URL or all URLs.
        
        Args:
            url: URL to get history for, or None for all URLs
            hours: Number of hours of history to retrieve
            
        Returns:
            Dictionary with uptime history information
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = {}
        
        # Process all URLs or just the specified one
        target_urls = [url] if url else list(uptime_history.keys())
        
        for target_url in target_urls:
            if target_url not in uptime_history:
                continue
                
            # Filter history by time
            history = [entry for entry in uptime_history[target_url] if entry[0] >= cutoff_time]
            
            # Calculate statistics
            total_checks = len(history)
            if total_checks == 0:
                result[target_url] = {
                    'uptime_percentage': 0,
                    'average_response_time': 0,
                    'checks': [],
                    'total_checks': 0,
                    'successful_checks': 0
                }
                continue
                
            successful_checks = sum(1 for entry in history if entry[3])  # entry[3] is is_up
            uptime_percentage = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
            
            # Calculate average response time for successful checks
            response_times = [entry[2] for entry in history if entry[3]]  # entry[2] is response_time
            average_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Format history for return
            formatted_history = [
                {
                    'timestamp': entry[0].isoformat(),
                    'status_code': entry[1],
                    'response_time': entry[2],
                    'is_up': entry[3]
                }
                for entry in history
            ]
            
            result[target_url] = {
                'uptime_percentage': uptime_percentage,
                'average_response_time': average_response_time,
                'checks': formatted_history,
                'total_checks': total_checks,
                'successful_checks': successful_checks
            }
        
        return result
    
    def export_uptime_metrics(self) -> Dict[str, Any]:
        """
        Export uptime metrics for all monitored endpoints.
        
        Returns:
            Dictionary with uptime metrics
        """
        metrics = {}
        
        for url, history in uptime_history.items():
            if not history:
                continue
                
            # Get metrics for different time periods
            for hours in [1, 24, 168]:  # 1 hour, 24 hours (1 day), 168 hours (7 days)
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                period_history = [entry for entry in history if entry[0] >= cutoff_time]
                
                if not period_history:
                    continue
                    
                # Calculate uptime percentage
                total_checks = len(period_history)
                successful_checks = sum(1 for entry in period_history if entry[3])
                uptime_percentage = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
                
                # Calculate average response time
                response_times = [entry[2] for entry in period_history if entry[3]]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                # Store metrics
                if url not in metrics:
                    metrics[url] = {}
                
                metrics[url][f"{hours}h"] = {
                    'uptime_percentage': uptime_percentage,
                    'average_response_time': avg_response_time,
                    'total_checks': total_checks,
                    'successful_checks': successful_checks,
                    'last_check_time': period_history[-1][0].isoformat() if period_history else None,
                    'last_check_success': period_history[-1][3] if period_history else None
                }
        
        return metrics


class UptimeRobotIntegration:
    """Integration with UptimeRobot service."""
    
    def __init__(self, config: Any):
        """
        Initialize UptimeRobot integration.
        
        Args:
            config: Application configuration with UptimeRobot API key
        """
        self.api_key = config.uptimerobot_api_key if hasattr(config, 'uptimerobot_api_key') else ""
        self.api_url = "https://api.uptimerobot.com/v2"
    
    def get_monitors(self) -> Dict[str, Any]:
        """
        Get all monitors from UptimeRobot.
        
        Returns:
            Dictionary with monitor information
        """
        if not self.api_key:
            logger.error("UptimeRobot API key not configured")
            return {"error": "API key not configured"}
        
        url = f"{self.api_url}/getMonitors"
        payload = {
            "api_key": self.api_key,
            "format": "json",
            "logs": 1
        }
        
        try:
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get monitors from UptimeRobot: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}"}
        
        except Exception as e:
            logger.error(f"Error getting monitors from UptimeRobot: {e}")
            return {"error": str(e)}
    
    def add_monitor(self, name: str, url: str, monitor_type: str = "HTTP", alert_contacts: str = "") -> Dict[str, Any]:
        """
        Add a new monitor to UptimeRobot.
        
        Args:
            name: Monitor friendly name
            url: URL to monitor
            monitor_type: Type of monitor (HTTP, keyword, ping, port, etc.)
            alert_contacts: Alert contact IDs, comma separated
            
        Returns:
            Dictionary with result information
        """
        if not self.api_key:
            logger.error("UptimeRobot API key not configured")
            return {"error": "API key not configured"}
        
        # Map monitor type to UptimeRobot type ID
        monitor_types = {
            "HTTP": 1,
            "keyword": 2,
            "ping": 3,
            "port": 4,
            "heartbeat": 5
        }
        
        type_id = monitor_types.get(monitor_type.upper(), 1)  # Default to HTTP
        
        url = f"{self.api_url}/newMonitor"
        payload = {
            "api_key": self.api_key,
            "format": "json",
            "type": type_id,
            "url": url,
            "friendly_name": name,
        }
        
        if alert_contacts:
            payload["alert_contacts"] = alert_contacts
        
        try:
            response = requests.post(url, data=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to add monitor to UptimeRobot: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}"}
        
        except Exception as e:
            logger.error(f"Error adding monitor to UptimeRobot: {e}")
            return {"error": str(e)}


class PingdomIntegration:
    """Integration with Pingdom service."""
    
    def __init__(self, config: Any):
        """
        Initialize Pingdom integration.
        
        Args:
            config: Application configuration with Pingdom API credentials
        """
        self.api_key = config.pingdom_api_key if hasattr(config, 'pingdom_api_key') else ""
        self.api_url = "https://api.pingdom.com/api/3.1"
    
    def get_checks(self) -> Dict[str, Any]:
        """
        Get all checks from Pingdom.
        
        Returns:
            Dictionary with check information
        """
        if not self.api_key:
            logger.error("Pingdom API key not configured")
            return {"error": "API key not configured"}
        
        url = f"{self.api_url}/checks"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get checks from Pingdom: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}"}
        
        except Exception as e:
            logger.error(f"Error getting checks from Pingdom: {e}")
            return {"error": str(e)}


class StatusCakeIntegration:
    """Integration with StatusCake service."""
    
    def __init__(self, config: Any):
        """
        Initialize StatusCake integration.
        
        Args:
            config: Application configuration with StatusCake API credentials
        """
        self.api_key = config.statuscake_api_key if hasattr(config, 'statuscake_api_key') else ""
        self.api_url = "https://api.statuscake.com/v1"
        self.username = config.statuscake_username if hasattr(config, 'statuscake_username') else ""
    
    def get_tests(self) -> Dict[str, Any]:
        """
        Get all tests from StatusCake.
        
        Returns:
            Dictionary with test information
        """
        if not self.api_key:
            logger.error("StatusCake API key not configured")
            return {"error": "API key not configured"}
        
        url = f"{self.api_url}/uptime"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get tests from StatusCake: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}"}
        
        except Exception as e:
            logger.error(f"Error getting tests from StatusCake: {e}")
            return {"error": str(e)}


def run_uptime_checks(config, notifier) -> None:
    """
    Run uptime checks for all registered endpoints.
    
    Args:
        config: Application configuration
        notifier: Notification service
    """
    logger.info("Running uptime checks")
    
    # Create monitor instance
    uptime_monitor = UptimeMonitor(config)
    
    # Register endpoints from configuration
    endpoints = []
    
    # Add Xenorize endpoints
    if hasattr(config, 'xenorize_api_url') and config.xenorize_api_url:
        # Add main API endpoint
        endpoints.append({
            'url': config.xenorize_api_url,
            'name': 'Xenorize API',
            'timeout': 10,
            'expected_status': 200,
            'headers': {'Authorization': f'Bearer {config.xenorize_api_key}'} if hasattr(config, 'xenorize_api_key') and config.xenorize_api_key else {}
        })
        
        # Add health endpoint if configured
        if hasattr(config, 'xenorize_health_endpoint') and config.xenorize_health_endpoint:
            endpoints.append({
                'url': f"{config.xenorize_api_url}{config.xenorize_health_endpoint}",
                'name': 'Xenorize Health',
                'timeout': 5,
                'expected_status': 200,
                'headers': {'Authorization': f'Bearer {config.xenorize_api_key}'} if hasattr(config, 'xenorize_api_key') and config.xenorize_api_key else {}
            })
    
    # Add Cryptellar endpoints
    if hasattr(config, 'cryptellar_api_url') and config.cryptellar_api_url:
        # Add main API endpoint
        endpoints.append({
            'url': config.cryptellar_api_url,
            'name': 'Cryptellar API',
            'timeout': 10,
            'expected_status': 200,
            'headers': {'Authorization': f'Bearer {config.cryptellar_api_key}'} if hasattr(config, 'cryptellar_api_key') and config.cryptellar_api_key else {}
        })
        
        # Add health endpoint if configured
        if hasattr(config, 'cryptellar_health_endpoint') and config.cryptellar_health_endpoint:
            endpoints.append({
                'url': f"{config.cryptellar_api_url}{config.cryptellar_health_endpoint}",
                'name': 'Cryptellar Health',
                'timeout': 5,
                'expected_status': 200,
                'headers': {'Authorization': f'Bearer {config.cryptellar_api_key}'} if hasattr(config, 'cryptellar_api_key') and config.cryptellar_api_key else {}
            })
    
    # Add custom endpoints from configuration
    if hasattr(config, 'uptime_monitor_endpoints'):
        for endpoint_config in config.uptime_monitor_endpoints:
            endpoints.append(endpoint_config)
    
    # Register endpoints
    uptime_monitor.register_endpoints(endpoints)
    
    # Run checks
    results = uptime_monitor.check_all_endpoints()
    
    # Process results and send notifications for failures
    for result in results:
        endpoint_name = result.get('endpoint', result.get('url', 'Unknown'))
        
        if not result.get('is_up', False):
            error_message = result.get('error', f"HTTP {result.get('status_code', 'unknown')}")
            
            logger.warning(f"Uptime check failed for {endpoint_name}: {error_message}")
            
            # Send notification
            notifier.send_alert(
                f"🚨 UPTIME FAILURE: {endpoint_name}\n\n"
                f"Error: {error_message}\n"
                f"URL: {result.get('url', 'N/A')}\n"
                f"Time: {result.get('timestamp', datetime.utcnow().isoformat())}"
            )
        else:
            logger.info(f"Uptime check passed for {endpoint_name}: {result.get('response_time', 0):.2f}s")
    
    # Update metrics for dashboard
    store_uptime_metrics(uptime_monitor.export_uptime_metrics())


def store_uptime_metrics(metrics: Dict[str, Any]) -> None:
    """
    Store uptime metrics in a file for later use by the dashboard.
    
    Args:
        metrics: Dictionary with uptime metrics
    """
    try:
        # Create directory if not exists
        os.makedirs('data', exist_ok=True)
        
        # Write metrics to file
        with open('data/uptime_metrics.json', 'w') as f:
            json.dump(metrics, f)
    except Exception as e:
        logger.error(f"Error storing uptime metrics: {e}")
