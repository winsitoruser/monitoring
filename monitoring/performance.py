"""
Performance monitoring module for system resource usage.
Tracks CPU, memory, and disk usage to ensure optimal performance.
"""
import logging
import psutil
import platform
from datetime import datetime
from typing import Dict, Any, Tuple

logger = logging.getLogger("monitoring.performance")

# Keep track of previous measurements for trend analysis
previous_measurements = {
    "cpu": 0,
    "memory": 0,
    "disk": 0,
    "timestamp": datetime.now()
}


def get_system_metrics() -> Dict[str, Any]:
    """
    Collect system performance metrics including CPU, memory, and disk usage.
    
    Returns:
        Dictionary with system metrics
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    metrics = {
        "timestamp": datetime.now(),
        "cpu": {
            "percent": cpu_percent,
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        },
        "system": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "uptime": datetime.now().timestamp() - psutil.boot_time(),
        }
    }
    
    # Update previous measurements for trend analysis
    global previous_measurements
    previous_measurements = {
        "cpu": cpu_percent,
        "memory": memory.percent,
        "disk": disk.percent,
        "timestamp": metrics["timestamp"]
    }
    
    return metrics


def analyze_performance(metrics: Dict[str, Any], config) -> Tuple[bool, str]:
    """
    Analyze system performance metrics and determine if there are any issues.
    
    Args:
        metrics: System metrics from get_system_metrics()
        config: Application configuration
        
    Returns:
        Tuple of (is_warning, warning_message)
    """
    warnings = []
    is_warning = False
    
    # Check CPU usage
    if metrics["cpu"]["percent"] > config.performance_warning_cpu:
        warnings.append(f"CPU usage is high: {metrics['cpu']['percent']}%")
        is_warning = True
        
    # Check memory usage
    if metrics["memory"]["percent"] > config.performance_warning_memory:
        warnings.append(f"Memory usage is high: {metrics['memory']['percent']}%")
        is_warning = True
        
    # Check disk usage (warning at 90%)
    if metrics["disk"]["percent"] > 90:
        warnings.append(f"Disk usage is high: {metrics['disk']['percent']}%")
        is_warning = True
    
    # Format the warning message
    warning_message = "\n".join(warnings) if warnings else ""
    
    return is_warning, warning_message


def check_system_performance(config, notifier) -> None:
    """
    Check system performance and send notifications if performance is poor.
    
    Args:
        config: Application configuration
        notifier: Notification service
    """
    logger.debug("Checking system performance")
    
    # Get current system metrics
    metrics = get_system_metrics()
    
    # Analyze the metrics
    is_warning, warning_message = analyze_performance(metrics, config)
    
    if is_warning:
        logger.warning(f"Performance warning: {warning_message}")
        
        # Create a detailed alert message
        alert_message = (
            f"⚠️ PERFORMANCE WARNING\n\n"
            f"{warning_message}\n\n"
            f"Current metrics:\n"
            f"- CPU: {metrics['cpu']['percent']}%\n"
            f"- Memory: {metrics['memory']['percent']}% "
            f"({metrics['memory']['used'] / (1024**3):.2f} GB used / "
            f"{metrics['memory']['total'] / (1024**3):.2f} GB total)\n"
            f"- Disk: {metrics['disk']['percent']}% "
            f"({metrics['disk']['used'] / (1024**3):.2f} GB used / "
            f"{metrics['disk']['total'] / (1024**3):.2f} GB total)\n"
            f"- System uptime: {metrics['system']['uptime'] / 3600:.2f} hours"
        )
        
        notifier.send_alert(alert_message)
    else:
        logger.debug(f"Performance check passed. CPU: {metrics['cpu']['percent']}%, "
                     f"Memory: {metrics['memory']['percent']}%, "
                     f"Disk: {metrics['disk']['percent']}%")
