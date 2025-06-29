"""
Dynamic Monitoring System that leverages Dynamic Configuration.
This module monitors targets specified in the dynamic configuration.
"""
import logging
import time
import asyncio
import threading
import json
import os
import requests
import socket
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.dynamic_config_manager import DynamicConfigManager
from utils.advanced_notification import NotificationManager

logger = logging.getLogger("monitoring.dynamic_monitor")

class DynamicMonitor:
    """
    Dynamic monitoring system that monitors targets specified in dynamic configuration.
    
    Features:
    - Automatic scheduling based on target configuration
    - Different checking strategies based on target type
    - Performance metrics collection
    - Alert generation on failure
    - Detailed logging of check results
    - Historical metrics storage
    """
    
    def __init__(self, config_manager: DynamicConfigManager, notification_manager: NotificationManager):
        """
        Initialize Dynamic Monitor.
        
        Args:
            config_manager: Dynamic Configuration Manager
            notification_manager: Notification Manager for sending alerts
        """
        self.config_manager = config_manager
        self.notification_manager = notification_manager
        self.stop_event = threading.Event()
        self.check_threads = {}
        self.metrics_dir = "data/dynamic_monitor/metrics"
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        logger.info("Initialized Dynamic Monitor")
        
    def start_monitoring(self):
        """Start monitoring all targets in the configuration."""
        logger.info("Starting dynamic monitoring")
        
        # Create a thread for the main monitoring loop
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Dynamic monitoring started")
        
    def stop_monitoring(self):
        """Stop all monitoring activities."""
        logger.info("Stopping dynamic monitoring")
        self.stop_event.set()
        
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
            
        logger.info("Dynamic monitoring stopped")
        
    def _monitoring_loop(self):
        """Main monitoring loop that schedules checks for all targets."""
        while not self.stop_event.is_set():
            try:
                # Get all targets
                targets = self.config_manager.get_all_targets()
                
                # Check which targets need to be monitored now
                current_time = time.time()
                
                for target_id, target in targets.items():
                    # Skip targets that already have threads running
                    if target_id in self.check_threads and self.check_threads[target_id].is_alive():
                        continue
                    
                    # Calculate when this target was last checked
                    last_check = None
                    if target["status"]["last_check"]:
                        try:
                            last_check_time = datetime.fromisoformat(target["status"]["last_check"]).timestamp()
                            if current_time - last_check_time < target["check_interval"]:
                                continue  # Not time to check yet
                        except (ValueError, TypeError):
                            pass  # If there's an error parsing, just check now
                    
                    # Create a thread to check this target
                    check_thread = threading.Thread(
                        target=self._check_target,
                        args=(target_id,)
                    )
                    check_thread.daemon = True
                    check_thread.start()
                    self.check_threads[target_id] = check_thread
                
                # Sleep for a short while before checking again
                # This interval determines how responsive the system is to config changes
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Back off on error
    
    def _check_target(self, target_id: str):
        """
        Check a specific target.
        
        Args:
            target_id: ID of the target to check
        """
        # Get the target configuration
        target = self.config_manager.get_target(target_id)
        if not target:
            logger.warning(f"Target {target_id} not found, skipping check")
            return
        
        target_type = target["type"]
        target_url = target["target"]
        
        logger.info(f"Checking {target['name']} ({target_url})")
        
        try:
            # Check based on target type
            if target_type == "api":
                check_result = self._check_api_target(target)
            elif target_type == "ip":
                check_result = self._check_ip_target(target)
            elif target_type == "hostname":
                check_result = self._check_hostname_target(target)
            else:
                logger.warning(f"Unknown target type: {target_type} for {target_url}")
                check_result = {
                    "status": "error",
                    "metrics": {
                        "error": f"Unknown target type: {target_type}"
                    }
                }
            
            # Update the target status
            self.config_manager.update_target_status(
                target_id, 
                check_result["status"], 
                check_result["metrics"]
            )
            
            # If status is not ok and we need to alert
            current_status = target["status"]["current_status"]
            failures = target["status"]["failures"]
            
            if check_result["status"] != "ok":
                if failures >= target["alert_threshold"] and current_status != "critical":
                    self._send_alert(target, check_result)
                elif failures > 0:
                    logger.warning(f"{target['name']} check failed ({failures}/{target['alert_threshold']}): {check_result['metrics'].get('error', 'Unknown error')}")
            elif current_status == "critical":
                # Was critical but now recovered
                self._send_recovery_alert(target)
                
            # Log metrics to file
            self._log_metrics(target_id, check_result["metrics"])
                
        except Exception as e:
            logger.error(f"Error checking {target['name']} ({target_url}): {e}")
            # Update status with error
            self.config_manager.update_target_status(
                target_id, 
                "error", 
                {"error": str(e)}
            )
    
    def _check_api_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check an API target.
        
        Args:
            target: Target configuration
            
        Returns:
            dict: Check result with status and metrics
        """
        url = target["target"]
        headers = target["headers"] or {}
        timeout = target.get("custom_params", {}).get("timeout", 10)
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=timeout)
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Get expected status code range
            expected_status = target.get("custom_params", {}).get("expected_status", "2xx")
            
            # Check if status code is in expected range
            if expected_status == "2xx" and 200 <= response.status_code < 300:
                status = "ok"
            elif expected_status == "3xx" and 300 <= response.status_code < 400:
                status = "ok"
            elif expected_status == "4xx" and 400 <= response.status_code < 500:
                status = "ok"
            elif str(response.status_code) == expected_status:
                status = "ok"
            else:
                status = "error"
            
            # Get response size
            content_length = len(response.content)
            
            # Collect metrics
            metrics = {
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "content_length": content_length,
                "content_type": response.headers.get("Content-Type"),
                "server": response.headers.get("Server"),
            }
            
            # Check for performance thresholds
            warning_threshold = target.get("custom_params", {}).get("warning_threshold_ms", 1000)
            critical_threshold = target.get("custom_params", {}).get("critical_threshold_ms", 3000)
            
            if response_time > critical_threshold:
                if status == "ok":
                    status = "warning"
                metrics["performance_status"] = "critical"
            elif response_time > warning_threshold:
                metrics["performance_status"] = "warning"
            else:
                metrics["performance_status"] = "ok"
                
            return {
                "status": status,
                "metrics": metrics
            }
            
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "metrics": {
                    "error": "Timed out",
                    "timeout": timeout
                }
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "metrics": {
                    "error": "Connection refused"
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "metrics": {
                    "error": str(e)
                }
            }
    
    def _check_ip_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check an IP target.
        
        Args:
            target: Target configuration
            
        Returns:
            dict: Check result with status and metrics
        """
        ip = target["target"]
        ping_count = target.get("custom_params", {}).get("ping_count", 3)
        
        try:
            # Use ping command to check if IP is reachable
            ping_params = '-n' if os.name == 'nt' else '-c'
            command = ['ping', ping_params, str(ping_count), ip]
            
            start_time = time.time()
            ping_process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = ping_process.communicate()
            end_time = time.time()
            
            # Parse ping output for response times
            response_times = []
            if os.name == 'nt':  # Windows
                for line in stdout.decode('utf-8').split('\n'):
                    if 'time=' in line:
                        try:
                            time_ms = float(line.split('time=')[1].split('ms')[0].strip())
                            response_times.append(time_ms)
                        except (ValueError, IndexError):
                            pass
            else:  # Unix
                for line in stdout.decode('utf-8').split('\n'):
                    if 'time=' in line:
                        try:
                            time_ms = float(line.split('time=')[1].split(' ms')[0].strip())
                            response_times.append(time_ms)
                        except (ValueError, IndexError):
                            pass
            
            if ping_process.returncode == 0:
                status = "ok"
                
                # Calculate metrics
                avg_response_time = sum(response_times) / len(response_times) if response_times else None
                min_response_time = min(response_times) if response_times else None
                max_response_time = max(response_times) if response_times else None
                
                metrics = {
                    "avg_response_time_ms": avg_response_time,
                    "min_response_time_ms": min_response_time,
                    "max_response_time_ms": max_response_time,
                    "packet_loss": 100 - (len(response_times) / ping_count * 100)
                }
                
                # Check for performance thresholds
                warning_threshold = target.get("custom_params", {}).get("warning_threshold_ms", 100)
                critical_threshold = target.get("custom_params", {}).get("critical_threshold_ms", 300)
                
                if avg_response_time and avg_response_time > critical_threshold:
                    metrics["performance_status"] = "critical"
                    status = "warning"  # Reachable but slow is a warning
                elif avg_response_time and avg_response_time > warning_threshold:
                    metrics["performance_status"] = "warning"
                else:
                    metrics["performance_status"] = "ok"
                
                # Check packet loss thresholds
                if metrics["packet_loss"] > 50:
                    metrics["packet_loss_status"] = "critical"
                    status = "warning"
                elif metrics["packet_loss"] > 10:
                    metrics["packet_loss_status"] = "warning"
                else:
                    metrics["packet_loss_status"] = "ok"
                    
            else:
                status = "error"
                metrics = {
                    "error": "Ping failed",
                    "returncode": ping_process.returncode,
                    "stderr": stderr.decode('utf-8')
                }
            
            return {
                "status": status,
                "metrics": metrics
            }
            
        except Exception as e:
            return {
                "status": "error",
                "metrics": {
                    "error": f"Ping error: {str(e)}"
                }
            }
    
    def _check_hostname_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check a hostname target.
        
        Args:
            target: Target configuration
            
        Returns:
            dict: Check result with status and metrics
        """
        hostname = target["target"]
        
        try:
            # Try to resolve the hostname
            start_time = time.time()
            ip = socket.gethostbyname(hostname)
            resolution_time = (time.time() - start_time) * 1000  # ms
            
            # Now ping the resolved IP
            ip_target = target.copy()
            ip_target["target"] = ip
            ip_check_result = self._check_ip_target(ip_target)
            
            # Add hostname resolution info to metrics
            ip_check_result["metrics"]["resolved_ip"] = ip
            ip_check_result["metrics"]["resolution_time_ms"] = resolution_time
            
            # If hostname resolution was successful but IP ping failed, still show it's a DNS issue
            if ip_check_result["status"] != "ok":
                ip_check_result["metrics"]["hostname_resolved"] = True
            
            return ip_check_result
            
        except socket.gaierror:
            return {
                "status": "error",
                "metrics": {
                    "error": "Failed to resolve hostname",
                    "hostname_resolved": False
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "metrics": {
                    "error": f"Hostname check error: {str(e)}",
                    "hostname_resolved": False
                }
            }
    
    def _send_alert(self, target: Dict[str, Any], check_result: Dict[str, Any]):
        """
        Send alert for a failed target.
        
        Args:
            target: Target configuration
            check_result: Check result with status and metrics
        """
        target_name = target["name"]
        target_url = target["target"]
        target_type = target["type"]
        
        # Format error message
        error_msg = check_result["metrics"].get("error", "Unknown error")
        
        # Build alert message
        if target_type == "api":
            status_code = check_result["metrics"].get("status_code", "N/A")
            response_time = check_result["metrics"].get("response_time_ms", "N/A")
            
            alert_message = (
                f"🚨 API ENDPOINT ALERT: {target_name}\n\n"
                f"URL: {target_url}\n"
                f"Status: {check_result['status']}\n"
                f"Status Code: {status_code}\n"
                f"Response Time: {response_time} ms\n"
                f"Error: {error_msg}\n\n"
                f"Failures: {target['status']['failures']}/{target['alert_threshold']}\n"
                f"Last Check: {target['status']['last_check']}"
            )
            
        elif target_type == "ip":
            alert_message = (
                f"🚨 IP ADDRESS ALERT: {target_name}\n\n"
                f"IP: {target_url}\n"
                f"Status: {check_result['status']}\n"
                f"Error: {error_msg}\n"
                f"Packet Loss: {check_result['metrics'].get('packet_loss', 'N/A')}%\n\n"
                f"Failures: {target['status']['failures']}/{target['alert_threshold']}\n"
                f"Last Check: {target['status']['last_check']}"
            )
            
        else:  # hostname
            alert_message = (
                f"🚨 HOSTNAME ALERT: {target_name}\n\n"
                f"Hostname: {target_url}\n"
                f"Status: {check_result['status']}\n"
                f"Error: {error_msg}\n"
                f"Resolved: {check_result['metrics'].get('hostname_resolved', False)}\n\n"
                f"Failures: {target['status']['failures']}/{target['alert_threshold']}\n"
                f"Last Check: {target['status']['last_check']}"
            )
        
        # Log the alert
        logger.error(f"Alert for {target_name}: {error_msg}")
        
        # Send alert through notification manager
        try:
            self.notification_manager.send_alert(
                alert_message,
                priority="high"
            )
        except Exception as e:
            logger.error(f"Failed to send alert for {target_name}: {e}")
    
    def _send_recovery_alert(self, target: Dict[str, Any]):
        """
        Send recovery alert for a target that was previously in critical state.
        
        Args:
            target: Target configuration
        """
        target_name = target["name"]
        target_url = target["target"]
        
        # Build recovery message
        recovery_message = (
            f"✅ RECOVERY ALERT: {target_name}\n\n"
            f"Target: {target_url}\n"
            f"Type: {target['type'].upper()}\n"
            f"Status: RECOVERED\n\n"
            f"The target is now responding normally after previous failures.\n"
            f"Last Check: {target['status']['last_check']}"
        )
        
        # Log the recovery
        logger.info(f"Recovery for {target_name}")
        
        # Send recovery through notification manager
        try:
            self.notification_manager.send_alert(
                recovery_message,
                priority="normal"
            )
        except Exception as e:
            logger.error(f"Failed to send recovery alert for {target_name}: {e}")
    
    def _log_metrics(self, target_id: str, metrics: Dict[str, Any]):
        """
        Log metrics to file for historical tracking.
        
        Args:
            target_id: ID of the target
            metrics: Metrics to log
        """
        try:
            # Create metrics directory for this target if it doesn't exist
            target_metrics_dir = os.path.join(self.metrics_dir, target_id)
            os.makedirs(target_metrics_dir, exist_ok=True)
            
            # Create a file for today's date
            today = datetime.now().strftime("%Y-%m-%d")
            metrics_file = os.path.join(target_metrics_dir, f"{today}.json")
            
            # Add timestamp to metrics
            metrics_with_timestamp = metrics.copy()
            metrics_with_timestamp["timestamp"] = datetime.now().isoformat()
            
            # Load existing metrics if file exists
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, 'r') as f:
                        daily_metrics = json.load(f)
                except json.JSONDecodeError:
                    daily_metrics = []
            else:
                daily_metrics = []
            
            # Append new metrics
            daily_metrics.append(metrics_with_timestamp)
            
            # Save back to file
            with open(metrics_file, 'w') as f:
                json.dump(daily_metrics, f, indent=2)
                
            # Limit file size (keep only latest 1000 entries)
            if len(daily_metrics) > 1000:
                with open(metrics_file, 'w') as f:
                    json.dump(daily_metrics[-1000:], f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log metrics for {target_id}: {e}")

# Function to run monitoring in main application
def run_dynamic_monitoring(config, notifier):
    """
    Run dynamic monitoring based on configuration.
    
    Args:
        config: Application configuration
        notifier: Notification service
    """
    # Create a dynamic configuration manager
    config_manager = DynamicConfigManager()
    
    # Create a notification manager from the regular notifier
    # This is a wrapper to make it compatible with the DynamicMonitor
    class NotifierWrapper:
        def send_alert(self, message, priority="normal"):
            notifier.send_alert(message)
    
    notification_wrapper = NotifierWrapper()
    
    # Create dynamic monitor
    monitor = DynamicMonitor(config_manager, notification_wrapper)
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Log that monitoring started
    logger.info("Started dynamic target monitoring")
    
    return monitor
