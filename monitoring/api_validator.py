"""
API Validator module for testing API endpoints beyond simple health checks.
Provides comprehensive validation of API functionality and data integrity.
"""
import logging
import requests
import json
import time
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("monitoring.api_validator")


class APIValidator:
    """
    Validates API endpoints to ensure they're functioning correctly.
    Goes beyond simple health checks to validate business logic and response data.
    """
    
    def __init__(self, base_url: str, api_key: str, service_name: str):
        """
        Initialize the API validator.
        
        Args:
            base_url: Base URL of the API
            api_key: API key for authentication
            service_name: Name of the service being validated
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.service_name = service_name
        self.headers = {"Authorization": f"Bearer {api_key}"}
        
    def validate_endpoint(self, 
                         endpoint: str, 
                         method: str = "GET", 
                         payload: Optional[Dict[str, Any]] = None,
                         expected_status: int = 200,
                         validation_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
                         timeout: int = 10) -> Dict[str, Any]:
        """
        Validate a specific API endpoint.
        
        Args:
            endpoint: API endpoint path (will be appended to base_url)
            method: HTTP method to use (GET, POST, etc.)
            payload: Request payload for POST/PUT methods
            expected_status: Expected HTTP status code
            validation_func: Optional function to validate response data
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with validation results
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=payload, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=payload, timeout=timeout)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported HTTP method: {method}",
                    "endpoint": endpoint,
                    "service": self.service_name
                }
                
            response_time = time.time() - start_time
            
            # Check status code
            status_ok = response.status_code == expected_status
            
            # Parse response data if JSON
            response_data = {}
            try:
                if response.content:
                    response_data = response.json()
            except json.JSONDecodeError:
                # Not JSON or invalid JSON
                pass
                
            # Run custom validation if provided
            validation_ok = True
            validation_error = None
            if validation_func and status_ok:
                try:
                    validation_ok = validation_func(response_data)
                    if not validation_ok:
                        validation_error = "Response data failed validation"
                except Exception as e:
                    validation_ok = False
                    validation_error = str(e)
            
            # Build result
            if status_ok and validation_ok:
                return {
                    "status": "ok",
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "endpoint": endpoint,
                    "service": self.service_name,
                    "data_sample": self._get_data_sample(response_data)
                }
            else:
                return {
                    "status": "error",
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "endpoint": endpoint,
                    "service": self.service_name,
                    "error": validation_error if not validation_ok else f"Unexpected status code: {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "error", 
                "error": "Request timed out", 
                "endpoint": endpoint, 
                "service": self.service_name
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error", 
                "error": "Connection failed", 
                "endpoint": endpoint, 
                "service": self.service_name
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e), 
                "endpoint": endpoint, 
                "service": self.service_name
            }
    
    def _get_data_sample(self, data: Any) -> Any:
        """
        Get a trimmed sample of response data for logging.
        Avoids logging excessive data volumes.
        
        Args:
            data: Response data to sample
            
        Returns:
            A sample of the data
        """
        if isinstance(data, dict):
            # Return just the keys for large dicts
            if len(data) > 5:
                return {"keys": list(data.keys())}
            return data
        elif isinstance(data, list):
            # Return just the first item for large lists
            if len(data) > 2:
                return data[:1]
            return data
        else:
            return data


class XenorizeAPIValidator(APIValidator):
    """Xenorize-specific API validator with custom validation rules."""
    
    def validate_all(self) -> List[Dict[str, Any]]:
        """
        Run all validations for Xenorize API.
        
        Returns:
            List of validation results
        """
        results = []
        
        # Basic health check
        results.append(self.validate_endpoint("health"))
        
        # Validate bot status endpoint
        results.append(self.validate_endpoint(
            "bot/status",
            validation_func=lambda data: "is_running" in data
        ))
        
        # Add more specific validations for Xenorize API
        # Example: validate user authentication
        results.append(self.validate_endpoint(
            "auth/verify",
            method="POST",
            payload={"token": self.api_key},
            validation_func=lambda data: data.get("authenticated") is True
        ))
        
        return results


class CryptellarAPIValidator(APIValidator):
    """Cryptellar-specific API validator with custom validation rules."""
    
    def validate_all(self) -> List[Dict[str, Any]]:
        """
        Run all validations for Cryptellar API.
        
        Returns:
            List of validation results
        """
        results = []
        
        # Basic health check
        results.append(self.validate_endpoint("health"))
        
        # Validate bot status endpoint
        results.append(self.validate_endpoint(
            "bot/status",
            validation_func=lambda data: "is_running" in data
        ))
        
        # Add more specific validations for Cryptellar API
        # Example: validate market data endpoint
        results.append(self.validate_endpoint(
            "market/summary",
            validation_func=lambda data: "timestamp" in data and "markets" in data
        ))
        
        return results


def run_api_validations(config, notifier) -> None:
    """
    Run comprehensive API validations for all configured services.
    
    Args:
        config: Application configuration
        notifier: Notification service for alerts
    """
    logger.info("Running API validations")
    
    all_results = []
    
    # Validate Xenorize API if configured
    if config.xenorize_api_url and config.xenorize_api_key:
        validator = XenorizeAPIValidator(
            config.xenorize_api_url,
            config.xenorize_api_key,
            "xenorize_api"
        )
        results = validator.validate_all()
        all_results.extend(results)
        
    # Validate Cryptellar API if configured
    if config.cryptellar_api_url and config.cryptellar_api_key:
        validator = CryptellarAPIValidator(
            config.cryptellar_api_url,
            config.cryptellar_api_key,
            "cryptellar_api"
        )
        results = validator.validate_all()
        all_results.extend(results)
    
    # Process results and send notifications for failures
    failures = [r for r in all_results if r["status"] != "ok"]
    
    if failures:
        logger.warning(f"API validation found {len(failures)} failures")
        
        # Group failures by service for better notification
        service_failures = {}
        for failure in failures:
            service = failure["service"]
            if service not in service_failures:
                service_failures[service] = []
            service_failures[service].append(failure)
        
        # Send notifications
        for service, service_failures in service_failures.items():
            alert_message = (
                f"🚨 API VALIDATION FAILURES: {service.upper()}\n\n"
            )
            
            for i, failure in enumerate(service_failures, 1):
                alert_message += (
                    f"{i}. Endpoint: {failure['endpoint']}\n"
                    f"   Error: {failure.get('error', 'Unknown error')}\n"
                    f"   Status: {failure.get('status_code', 'N/A')}\n\n"
                )
            
            notifier.send_alert(alert_message)
    else:
        logger.info("All API validations passed successfully")
