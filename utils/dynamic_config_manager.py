"""
Dynamic Configuration Manager for the Monitoring System.
Allows for runtime addition and management of monitoring targets without service restart.
"""
import json
import os
import logging
import ipaddress
import requests
import uuid
import threading
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

logger = logging.getLogger("utils.dynamic_config")

class DynamicConfigManager:
    """
    Dynamic Configuration Manager for monitoring targets.
    
    Features:
    - Add/remove monitoring targets (API endpoints, IP addresses) at runtime
    - Auto-detection of endpoint type
    - HTTP health check customization
    - Persistent configuration storage
    - Group-based organization
    - Rate limiting protection for API endpoints
    - Dynamic alert thresholds
    """
    
    def __init__(self, config_path="data/dynamic_config"):
        """
        Initialize the Dynamic Configuration Manager.
        
        Args:
            config_path: Path where configuration files will be stored
        """
        self.config_path = config_path
        self.targets = {}
        self.lock = threading.RLock()
        self.auto_discovery_enabled = False
        
        # Create configuration directory if it doesn't exist
        os.makedirs(self.config_path, exist_ok=True)
        
        # Load existing configuration if available
        self._load_config()

    def _load_config(self):
        """Load existing configuration from disk."""
        try:
            config_file = os.path.join(self.config_path, "targets.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.targets = json.load(f)
                logger.info(f"Loaded {len(self.targets)} monitoring targets")
            else:
                logger.info("No existing targets configuration found")
        except Exception as e:
            logger.error(f"Error loading targets configuration: {e}")
            self.targets = {}
    
    def _save_config(self):
        """Save current configuration to disk."""
        try:
            with self.lock:
                config_file = os.path.join(self.config_path, "targets.json")
                with open(config_file, 'w') as f:
                    json.dump(self.targets, f, indent=2)
                logger.info(f"Saved {len(self.targets)} monitoring targets")
                
                # Also save a timestamped backup
                backup_dir = os.path.join(self.config_path, "backups")
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(backup_dir, f"targets_{timestamp}.json")
                with open(backup_file, 'w') as f:
                    json.dump(self.targets, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving targets configuration: {e}")

    def _validate_target(self, target):
        """
        Validate and auto-detect the target type.
        
        Returns:
            dict: Target info with detected type, status
        """
        target_type = "unknown"
        detect_status = "unknown"
        additional_info = {}
        
        # Check if it's an IP address
        try:
            ip = ipaddress.ip_address(target)
            target_type = "ip"
            detect_status = "success"
        except ValueError:
            # Check if it's a URL/API endpoint
            if target.startswith(("http://", "https://")):
                target_type = "api"
                try:
                    # Try to connect with a short timeout
                    response = requests.get(target, timeout=3)
                    detect_status = "success"
                    additional_info = {
                        "status_code": response.status_code,
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "content_type": response.headers.get("Content-Type", "")
                    }
                except requests.RequestException as e:
                    detect_status = "error"
                    additional_info = {"error": str(e)}
            else:
                # Assume it's a hostname
                target_type = "hostname"
                try:
                    # Try to resolve hostname
                    ip = ipaddress.ip_address(socket.gethostbyname(target))
                    detect_status = "success"
                    additional_info = {"resolved_ip": str(ip)}
                except Exception as e:
                    detect_status = "error"
                    additional_info = {"error": str(e)}
        
        return {
            "type": target_type,
            "detection_status": detect_status,
            "additional_info": additional_info
        }

    def add_target(self, target: str, name: Optional[str] = None, 
                  group: str = "default", check_interval: int = 60,
                  alert_threshold: int = 3, headers: Optional[Dict] = None,
                  custom_params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Add a new monitoring target.
        
        Args:
            target: URL, IP address or hostname to monitor
            name: Friendly name for the target
            group: Group to categorize the target
            check_interval: How often to check the target, in seconds
            alert_threshold: Number of failures before alerting
            headers: HTTP headers to use when checking API endpoints
            custom_params: Additional parameters for specific monitoring
            
        Returns:
            dict: Information about the added target
        """
        with self.lock:
            target_id = str(uuid.uuid4())
            
            # Auto-detect target type
            detection_info = self._validate_target(target)
            
            # Create a name if not provided
            if not name:
                if detection_info["type"] == "api":
                    name = f"API: {target.split('//')[1].split('/')[0]}"
                elif detection_info["type"] == "ip":
                    name = f"IP: {target}"
                else:
                    name = f"Host: {target}"
            
            # Create target configuration
            target_config = {
                "id": target_id,
                "name": name,
                "target": target,
                "type": detection_info["type"],
                "group": group,
                "check_interval": check_interval,
                "alert_threshold": alert_threshold,
                "headers": headers or {},
                "custom_params": custom_params or {},
                "status": {
                    "last_check": None,
                    "current_status": "pending",
                    "failures": 0,
                    "last_success": None,
                    "last_failure": None,
                    "metrics": []
                },
                "created_at": datetime.now().isoformat(),
                "detection_info": detection_info
            }
            
            # Add to targets collection
            self.targets[target_id] = target_config
            
            # Save updated configuration
            self._save_config()
            
            logger.info(f"Added new monitoring target: {name} ({target})")
            return target_config
    
    def remove_target(self, target_id: str) -> bool:
        """
        Remove a monitoring target.
        
        Args:
            target_id: ID of the target to remove
            
        Returns:
            bool: Whether the removal was successful
        """
        with self.lock:
            if target_id in self.targets:
                target_info = self.targets[target_id]
                del self.targets[target_id]
                self._save_config()
                logger.info(f"Removed monitoring target: {target_info['name']} ({target_info['target']})")
                return True
            return False
    
    def get_target(self, target_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific target.
        
        Args:
            target_id: ID of the target to get
            
        Returns:
            dict: Target configuration, or None if not found
        """
        return self.targets.get(target_id)
    
    def get_all_targets(self) -> Dict[str, Any]:
        """
        Get all monitoring targets.
        
        Returns:
            dict: All targets with their configurations
        """
        return self.targets
    
    def get_targets_by_group(self, group: str) -> Dict[str, Any]:
        """
        Get all targets in a specific group.
        
        Args:
            group: Group name to filter by
            
        Returns:
            dict: Targets in the specified group
        """
        return {k: v for k, v in self.targets.items() if v.get("group") == group}
    
    def get_targets_by_type(self, target_type: str) -> Dict[str, Any]:
        """
        Get all targets of a specific type.
        
        Args:
            target_type: Type to filter by (api, ip, hostname)
            
        Returns:
            dict: Targets of the specified type
        """
        return {k: v for k, v in self.targets.items() if v.get("type") == target_type}
    
    def update_target_status(self, target_id: str, 
                           status: str, metrics: Dict[str, Any]) -> bool:
        """
        Update the status and metrics for a target.
        
        Args:
            target_id: ID of the target to update
            status: Current status (ok, warning, critical)
            metrics: Performance/health metrics from latest check
            
        Returns:
            bool: Whether the update was successful
        """
        with self.lock:
            if target_id not in self.targets:
                return False
            
            target = self.targets[target_id]
            
            # Update status information
            now = datetime.now().isoformat()
            target["status"]["last_check"] = now
            
            # Update failure count and status
            if status != "ok":
                target["status"]["failures"] += 1
                target["status"]["last_failure"] = now
                if target["status"]["failures"] >= target["alert_threshold"]:
                    target["status"]["current_status"] = "critical"
                else:
                    target["status"]["current_status"] = "warning"
            else:
                target["status"]["failures"] = 0
                target["status"]["current_status"] = "ok"
                target["status"]["last_success"] = now
            
            # Append metrics (keep last 100 entries)
            metrics["timestamp"] = now
            target["status"]["metrics"].append(metrics)
            if len(target["status"]["metrics"]) > 100:
                target["status"]["metrics"].pop(0)
            
            # Periodic save (not every update to avoid disk I/O)
            if target["status"]["failures"] == 0 or target["status"]["failures"] >= target["alert_threshold"]:
                self._save_config()
                
            return True
    
    def update_target_config(self, target_id: str, 
                           config_updates: Dict[str, Any]) -> bool:
        """
        Update configuration for a target.
        
        Args:
            target_id: ID of the target to update
            config_updates: Configuration items to update
            
        Returns:
            bool: Whether the update was successful
        """
        with self.lock:
            if target_id not in self.targets:
                return False
            
            # Only allow updating certain fields
            allowed_updates = [
                "name", "check_interval", "alert_threshold", 
                "headers", "custom_params", "group"
            ]
            
            target = self.targets[target_id]
            for key, value in config_updates.items():
                if key in allowed_updates:
                    target[key] = value
            
            self._save_config()
            logger.info(f"Updated configuration for target: {target['name']} ({target['target']})")
            return True
    
    def enable_auto_discovery(self, enabled: bool = True) -> None:
        """
        Enable or disable auto-discovery of related endpoints.
        
        Args:
            enabled: Whether auto-discovery should be enabled
        """
        self.auto_discovery_enabled = enabled
    
    def discover_related_targets(self, target_id: str) -> List[Dict[str, Any]]:
        """
        Discover related targets from an existing target.
        
        Args:
            target_id: ID of the target to discover relations for
            
        Returns:
            list: Discovered potential targets
        """
        if not self.auto_discovery_enabled:
            return []
        
        discovered = []
        if target_id in self.targets:
            target = self.targets[target_id]
            
            # Implement discovery logic based on target type
            if target["type"] == "api":
                # For APIs, parse response for links or related endpoints
                pass
            elif target["type"] in ["ip", "hostname"]:
                # For IPs/hostnames, try common ports
                pass
                
        return discovered

    def export_config(self, format_type: str = "json") -> str:
        """
        Export the current configuration.
        
        Args:
            format_type: Format to export as (json, yaml)
            
        Returns:
            str: Configuration in the requested format
        """
        if format_type == "json":
            return json.dumps(self.targets, indent=2)
        else:
            # Implement other formats as needed
            return json.dumps(self.targets, indent=2)
    
    def import_config(self, config_data: str, format_type: str = "json") -> bool:
        """
        Import configuration data.
        
        Args:
            config_data: Configuration data to import
            format_type: Format of the imported data
            
        Returns:
            bool: Whether the import was successful
        """
        try:
            if format_type == "json":
                imported_targets = json.loads(config_data)
            else:
                # Implement other formats as needed
                return False
                
            with self.lock:
                self.targets.update(imported_targets)
                self._save_config()
                
            logger.info(f"Imported {len(imported_targets)} targets")
            return True
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False
