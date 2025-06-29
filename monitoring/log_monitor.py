"""
Application Log Monitoring module.
Provides integration with log monitoring systems like ELK Stack, Graylog, Fluentd, or Papertrail.
"""
import logging
import json
import socket
import os
import re
import time
from datetime import datetime
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger("monitoring.log_monitor")

class LogMonitorBase:
    """Base class for log monitoring integrations."""
    
    def __init__(self, config: Any):
        """
        Initialize the log monitor.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.host = socket.gethostname()
        self.app_name = config.app_name if hasattr(config, 'app_name') else "monitoring-service"
    
    def format_log_entry(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format a log entry for sending to the log monitoring system.
        
        Args:
            level: Log level (info, warning, error, critical)
            message: Log message
            metadata: Additional metadata to include
            
        Returns:
            Formatted log entry as dictionary
        """
        log_entry = {
            "@timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "host": self.host,
            "application": self.app_name,
        }
        
        if metadata:
            log_entry["metadata"] = metadata
        
        return log_entry
    
    def send_log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a log entry to the monitoring system.
        
        Args:
            level: Log level (info, warning, error, critical)
            message: Log message
            metadata: Additional metadata to include
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("This method should be implemented by subclasses")


class ElasticsearchLogMonitor(LogMonitorBase):
    """Integration with Elasticsearch for log monitoring."""
    
    def __init__(self, config: Any):
        """
        Initialize the Elasticsearch log monitor.
        
        Args:
            config: Application configuration containing Elasticsearch settings
        """
        super().__init__(config)
        self.elasticsearch_url = config.elasticsearch_url if hasattr(config, 'elasticsearch_url') else ""
        self.elasticsearch_index = config.elasticsearch_index if hasattr(config, 'elasticsearch_index') else "monitoring-logs"
        self.elasticsearch_auth = None
        
        # Setup authentication if credentials are provided
        if hasattr(config, 'elasticsearch_user') and hasattr(config, 'elasticsearch_password'):
            if config.elasticsearch_user and config.elasticsearch_password:
                self.elasticsearch_auth = (config.elasticsearch_user, config.elasticsearch_password)
    
    def send_log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a log entry to Elasticsearch.
        
        Args:
            level: Log level (info, warning, error, critical)
            message: Log message
            metadata: Additional metadata to include
            
        Returns:
            True if successful, False otherwise
        """
        if not self.elasticsearch_url:
            logger.warning("Elasticsearch URL not configured")
            return False
        
        log_entry = self.format_log_entry(level, message, metadata)
        url = f"{self.elasticsearch_url}/{self.elasticsearch_index}/_doc"
        
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                url, 
                json=log_entry,
                headers=headers,
                auth=self.elasticsearch_auth,
                timeout=5
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.debug(f"Log sent to Elasticsearch: {message}")
                return True
            else:
                logger.error(f"Failed to send log to Elasticsearch. Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending log to Elasticsearch: {e}")
            return False


class GraylogMonitor(LogMonitorBase):
    """Integration with Graylog for log monitoring."""
    
    def __init__(self, config: Any):
        """
        Initialize the Graylog monitor.
        
        Args:
            config: Application configuration containing Graylog settings
        """
        super().__init__(config)
        self.graylog_url = config.graylog_url if hasattr(config, 'graylog_url') else ""
        self.graylog_port = config.graylog_port if hasattr(config, 'graylog_port') else 12201
        self.graylog_use_https = config.graylog_use_https if hasattr(config, 'graylog_use_https') else False
        
    def send_log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a log entry to Graylog using GELF HTTP API.
        
        Args:
            level: Log level (info, warning, error, critical)
            message: Log message
            metadata: Additional metadata to include
            
        Returns:
            True if successful, False otherwise
        """
        if not self.graylog_url:
            logger.warning("Graylog URL not configured")
            return False
        
        # Convert log level to numeric (following Syslog severity levels)
        level_numbers = {
            "debug": 7,
            "info": 6,
            "warning": 4,
            "error": 3,
            "critical": 2
        }
        
        # Create GELF format message
        gelf_message = {
            "version": "1.1",
            "host": self.host,
            "short_message": message,
            "timestamp": time.time(),
            "level": level_numbers.get(level.lower(), 6),
            "_application": self.app_name,
        }
        
        # Add metadata fields with underscore prefix as per GELF spec
        if metadata:
            for key, value in metadata.items():
                gelf_message[f"_{key}"] = value
        
        # Construct the URL
        protocol = "https" if self.graylog_use_https else "http"
        url = f"{protocol}://{self.graylog_url}:{self.graylog_port}/gelf"
        
        try:
            response = requests.post(
                url,
                json=gelf_message,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.debug(f"Log sent to Graylog: {message}")
                return True
            else:
                logger.error(f"Failed to send log to Graylog. Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending log to Graylog: {e}")
            return False


class FluentdMonitor(LogMonitorBase):
    """Integration with Fluentd for log monitoring."""
    
    def __init__(self, config: Any):
        """
        Initialize the Fluentd monitor.
        
        Args:
            config: Application configuration containing Fluentd settings
        """
        super().__init__(config)
        self.fluentd_url = config.fluentd_url if hasattr(config, 'fluentd_url') else ""
        self.fluentd_tag = config.fluentd_tag if hasattr(config, 'fluentd_tag') else "monitoring"
        
    def send_log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a log entry to Fluentd HTTP endpoint.
        
        Args:
            level: Log level (info, warning, error, critical)
            message: Log message
            metadata: Additional metadata to include
            
        Returns:
            True if successful, False otherwise
        """
        if not self.fluentd_url:
            logger.warning("Fluentd URL not configured")
            return False
        
        log_entry = self.format_log_entry(level, message, metadata)
        url = f"{self.fluentd_url}/{self.fluentd_tag}"
        
        try:
            response = requests.post(
                url,
                json=log_entry,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.debug(f"Log sent to Fluentd: {message}")
                return True
            else:
                logger.error(f"Failed to send log to Fluentd. Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending log to Fluentd: {e}")
            return False


class PapertrailMonitor(LogMonitorBase):
    """Integration with Papertrail for log monitoring."""
    
    def __init__(self, config: Any):
        """
        Initialize the Papertrail monitor.
        
        Args:
            config: Application configuration containing Papertrail settings
        """
        super().__init__(config)
        self.papertrail_host = config.papertrail_host if hasattr(config, 'papertrail_host') else ""
        self.papertrail_port = config.papertrail_port if hasattr(config, 'papertrail_port') else 0
        
        # Setup UDP socket for Papertrail
        if self.papertrail_host and self.papertrail_port:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            except Exception as e:
                logger.error(f"Failed to create UDP socket for Papertrail: {e}")
                self.socket = None
        else:
            self.socket = None
    
    def send_log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a log entry to Papertrail via syslog over UDP.
        
        Args:
            level: Log level (info, warning, error, critical)
            message: Log message
            metadata: Additional metadata to include
            
        Returns:
            True if successful, False otherwise
        """
        if not self.socket:
            logger.warning("Papertrail connection not configured")
            return False
        
        # Convert level to syslog priority
        priorities = {
            "debug": 7,
            "info": 6,
            "warning": 4,
            "error": 3,
            "critical": 2
        }
        priority = priorities.get(level.lower(), 6)
        
        # Format according to syslog RFC
        timestamp = datetime.utcnow().strftime("%b %d %H:%M:%S")
        program = self.app_name
        
        # Include metadata if present
        metadata_str = ""
        if metadata:
            metadata_str = " " + json.dumps(metadata)
        
        # Construct the syslog message
        syslog_message = f"<{priority}>{timestamp} {self.host} {program}: [{level.upper()}] {message}{metadata_str}"
        
        try:
            self.socket.sendto(syslog_message.encode('utf-8'), (self.papertrail_host, self.papertrail_port))
            logger.debug(f"Log sent to Papertrail: {message}")
            return True
        except Exception as e:
            logger.error(f"Error sending log to Papertrail: {e}")
            return False


class LogMonitoringManager:
    """Manager class to handle different log monitoring integrations."""
    
    def __init__(self, config: Any):
        """
        Initialize the log monitoring manager with configured systems.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.monitors = []
        
        # Initialize enabled log monitoring systems
        if hasattr(config, 'log_monitor_elasticsearch_enabled') and config.log_monitor_elasticsearch_enabled:
            self.monitors.append(ElasticsearchLogMonitor(config))
            
        if hasattr(config, 'log_monitor_graylog_enabled') and config.log_monitor_graylog_enabled:
            self.monitors.append(GraylogMonitor(config))
            
        if hasattr(config, 'log_monitor_fluentd_enabled') and config.log_monitor_fluentd_enabled:
            self.monitors.append(FluentdMonitor(config))
            
        if hasattr(config, 'log_monitor_papertrail_enabled') and config.log_monitor_papertrail_enabled:
            self.monitors.append(PapertrailMonitor(config))
    
    def send_log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Send a log entry to all configured log monitoring systems.
        
        Args:
            level: Log level (info, warning, error, critical)
            message: Log message
            metadata: Additional metadata to include
        """
        for monitor in self.monitors:
            try:
                monitor.send_log(level, message, metadata)
            except Exception as e:
                logger.error(f"Error sending log to monitor {monitor.__class__.__name__}: {e}")
    
    def collect_and_forward_logs(self, log_path: str, since_seconds: int = 300) -> Dict[str, Any]:
        """
        Collect recent logs from a log file and forward them to monitoring systems.
        
        Args:
            log_path: Path to the log file
            since_seconds: Only collect logs from the last X seconds
            
        Returns:
            Dictionary with collection status and counts
        """
        if not os.path.exists(log_path):
            logger.error(f"Log file not found: {log_path}")
            return {"status": "error", "message": "Log file not found", "count": 0}
        
        try:
            # Get file modified time and current time
            file_mtime = os.path.getmtime(log_path)
            current_time = time.time()
            
            # Skip if file is older than since_seconds
            if current_time - file_mtime > since_seconds:
                return {"status": "skipped", "message": "Log file too old", "count": 0}
            
            # Read the log file
            with open(log_path, 'r') as f:
                log_lines = f.readlines()
            
            # Regular expression to parse log entries
            # Format example: [2023-06-28 15:30:45,123] [INFO] [module.name] Message text
            log_pattern = r'\[(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3})\]\s\[(\w+)\]\s\[([^\]]+)\]\s(.*)'
            
            count = 0
            for line in log_lines:
                match = re.match(log_pattern, line.strip())
                if match:
                    timestamp_str, level, module, message = match.groups()
                    
                    # Convert timestamp string to timestamp
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                        log_time = timestamp.timestamp()
                        
                        # Only process recent logs
                        if current_time - log_time <= since_seconds:
                            # Send to log monitoring systems
                            metadata = {"module": module}
                            self.send_log(level.lower(), message, metadata)
                            count += 1
                    except Exception as e:
                        logger.error(f"Error parsing timestamp: {e}")
            
            return {"status": "success", "message": f"Processed {count} log entries", "count": count}
        
        except Exception as e:
            logger.error(f"Error collecting logs: {e}")
            return {"status": "error", "message": str(e), "count": 0}


def send_application_log(log_manager: LogMonitoringManager, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Send an application log entry to all configured monitoring systems.
    
    Args:
        log_manager: LogMonitoringManager instance
        level: Log level (info, warning, error, critical)
        message: Log message
        metadata: Additional metadata to include
    """
    log_manager.send_log(level, message, metadata)


def run_log_forwarding(config, log_manager: LogMonitoringManager) -> None:
    """
    Run the log forwarding process for configured log files.
    
    Args:
        config: Application configuration
        log_manager: LogMonitoringManager instance
    """
    logger.info("Running log forwarding")
    
    # Get log files to monitor
    log_files = []
    if hasattr(config, 'log_monitor_files'):
        log_files = config.log_monitor_files
    else:
        # Default log files
        log_dir = os.path.join(os.getcwd(), 'logs')
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    log_files.append(os.path.join(log_dir, filename))
    
    # Process each log file
    for log_file in log_files:
        try:
            result = log_manager.collect_and_forward_logs(log_file)
            if result["status"] == "success" and result["count"] > 0:
                logger.info(f"Forwarded {result['count']} log entries from {log_file}")
        except Exception as e:
            logger.error(f"Error forwarding logs from {log_file}: {e}")
