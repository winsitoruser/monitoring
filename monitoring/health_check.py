"""
Health check module for Xenorize and Cryptellar services.
Monitors API endpoints, bot functionality, and service availability.
"""
import logging
import time
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger("monitoring.health_check")

# Status tracking for consecutive failures
service_status = {
    "xenorize_api": {"failures": 0, "last_status": "unknown"},
    "xenorize_bot": {"failures": 0, "last_status": "unknown"},
    "cryptellar_api": {"failures": 0, "last_status": "unknown"},
    "cryptellar_bot": {"failures": 0, "last_status": "unknown"},
}


def check_api_health(url: str, api_key: str, service_name: str) -> Dict[str, Any]:
    """
    Check if the API is accessible and responding correctly.
    
    Args:
        url: The API endpoint URL
        api_key: API authentication key
        service_name: Name of the service being checked
    
    Returns:
        Dict with status information
    """
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        # Add a health check endpoint to the URL
        health_url = f"{url}/health" if not url.endswith('/health') else url
        
        start_time = time.time()
        response = requests.get(health_url, headers=headers, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            return {
                "status": "ok",
                "response_time": response_time,
                "details": response.json() if response.content else {},
                "service": service_name
            }
        else:
            return {
                "status": "error",
                "response_time": response_time,
                "status_code": response.status_code,
                "error": f"API returned {response.status_code}",
                "service": service_name
            }
    except requests.exceptions.Timeout:
        return {"status": "error", "error": "Request timed out", "service": service_name}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error": "Connection failed", "service": service_name}
    except Exception as e:
        return {"status": "error", "error": str(e), "service": service_name}


def check_bot_health(service_name: str, config) -> Dict[str, Any]:
    """
    Check if the bots are running and functioning.
    
    This would typically involve checking if bot processes are running,
    or making API calls to the bot's endpoints.
    
    Args:
        service_name: Name of the bot service to check
        config: Configuration object with service details
        
    Returns:
        Dict with status information
    """
    # In a real implementation, this would check if the bot is actually running
    # For now, we'll implement a placeholder that checks service-specific endpoints
    try:
        if service_name == "xenorize_bot":
            # Example implementation: check a bot-specific endpoint
            url = f"{config.xenorize_api_url}/bot/status"
            response = requests.get(
                url, 
                headers={"Authorization": f"Bearer {config.xenorize_api_key}"}, 
                timeout=10
            )
        elif service_name == "cryptellar_bot":
            url = f"{config.cryptellar_api_url}/bot/status"
            response = requests.get(
                url, 
                headers={"Authorization": f"Bearer {config.cryptellar_api_key}"}, 
                timeout=10
            )
        else:
            return {"status": "error", "error": f"Unknown service: {service_name}", "service": service_name}
        
        if response.status_code == 200:
            bot_data = response.json()
            return {
                "status": "ok" if bot_data.get("is_running", False) else "error",
                "details": bot_data,
                "service": service_name
            }
        else:
            return {
                "status": "error",
                "error": f"Bot status check failed with code {response.status_code}",
                "service": service_name
            }
            
    except Exception as e:
        return {"status": "error", "error": str(e), "service": service_name}


def process_health_check_result(result: Dict[str, Any], config, notifier) -> None:
    """
    Process the result of a health check and trigger notifications if needed.
    
    Args:
        result: Health check result dictionary
        config: Application configuration
        notifier: Notification service
    """
    service_name = result.get("service")
    status = result.get("status")
    
    if status != "ok":
        service_status[service_name]["failures"] += 1
        failure_count = service_status[service_name]["failures"]
        error_message = result.get("error", "Unknown error")
        
        logger.warning(f"{service_name} health check failed ({failure_count} consecutive failures): {error_message}")
        
        # Check if we should send an alert based on threshold
        if failure_count >= config.alert_threshold and service_status[service_name]["last_status"] != "error":
            alert_message = (
                f"🚨 {service_name.upper()} SERVICE FAILURE\n\n"
                f"Consecutive failures: {failure_count}\n"
                f"Error: {error_message}"
            )
            notifier.send_alert(alert_message)
            service_status[service_name]["last_status"] = "error"
    else:
        # If service was previously failing but is now OK, send recovery notification
        if service_status[service_name]["failures"] >= config.alert_threshold:
            recovery_message = f"✅ {service_name.upper()} SERVICE RECOVERED after {service_status[service_name]['failures']} failures"
            notifier.send_alert(recovery_message)
            
        # Reset failure counter
        service_status[service_name]["failures"] = 0
        service_status[service_name]["last_status"] = "ok"
        
        logger.info(f"{service_name} health check passed. Response time: {result.get('response_time', 'N/A')}s")


def run_health_checks(config, notifier) -> None:
    """
    Run all health checks for Xenorize and Cryptellar services.
    
    Args:
        config: Application configuration
        notifier: Notification service for alerts
    """
    logger.info("Running health checks")
    
    # Check Xenorize services
    xenorize_api_result = check_api_health(
        config.xenorize_api_url, 
        config.xenorize_api_key,
        "xenorize_api"
    )
    process_health_check_result(xenorize_api_result, config, notifier)
    
    xenorize_bot_result = check_bot_health("xenorize_bot", config)
    process_health_check_result(xenorize_bot_result, config, notifier)
    
    # Check Cryptellar services
    cryptellar_api_result = check_api_health(
        config.cryptellar_api_url,
        config.cryptellar_api_key,
        "cryptellar_api"
    )
    process_health_check_result(cryptellar_api_result, config, notifier)
    
    cryptellar_bot_result = check_bot_health("cryptellar_bot", config)
    process_health_check_result(cryptellar_bot_result, config, notifier)
