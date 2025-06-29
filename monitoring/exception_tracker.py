"""
Exception tracking module for monitoring unhandled exceptions in Xenorize and Cryptellar services.
Sets up global exception hooks and provides custom exception handling with notifications.
"""
import logging
import sys
import traceback
from functools import wraps
from typing import Callable, Any, Dict, Type, Optional

logger = logging.getLogger("monitoring.exception_tracker")


class CustomExceptionTracker:
    """
    Custom exception tracker to monitor and report exceptions in the applications.
    """
    def __init__(self, notifier=None):
        self.notifier = notifier
        self.exception_counts: Dict[str, int] = {}
    
    def handle_exception(self, exc_type: Type[Exception], exc_value: Exception, exc_traceback) -> None:
        """
        Handle uncaught exceptions and report them to notification channels.
        
        Args:
            exc_type: Exception class
            exc_value: Exception instance
            exc_traceback: Traceback object
        """
        # Skip KeyboardInterrupt to allow clean program termination
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Get exception details
        exception_name = exc_type.__name__
        exception_message = str(exc_value)
        
        # Get the traceback as a string
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = ''.join(tb_lines)
        
        # Count exception occurrences
        self.exception_counts[exception_name] = self.exception_counts.get(exception_name, 0) + 1
        
        # Log the exception
        logger.error(f"Uncaught exception: {exception_name}: {exception_message}\n{tb_text}")
        
        # Notify via configured channels
        if self.notifier:
            alert_message = (
                f"🚨 EXCEPTION DETECTED: {exception_name}\n\n"
                f"Message: {exception_message}\n"
                f"Occurrences: {self.exception_counts[exception_name]}\n\n"
                f"Traceback (most recent call):\n"
                f"```\n{tb_lines[-3].strip()}\n{tb_lines[-2].strip()}\n```"
            )
            self.notifier.send_alert(alert_message)


def exception_handler(func: Callable) -> Callable:
    """
    Decorator to catch and log exceptions that occur in decorated functions.
    
    Args:
        func: The function to wrap with exception handling
        
    Returns:
        Wrapped function with exception handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {str(e)}")
            
            # Get the traceback as a string
            tb_text = traceback.format_exc()
            
            # Extract calling module/class if possible
            module_name = func.__module__
            
            # If the first arg is self, try to get the class name
            class_name = ""
            if args and hasattr(args[0], "__class__"):
                class_name = args[0].__class__.__name__ + "."
                
            # Log full traceback
            logger.debug(f"Exception traceback in {module_name}.{class_name}{func.__name__}:\n{tb_text}")
            
            # Re-raise the exception for proper handling by global handler
            raise
    
    return wrapper


def setup_exception_tracking(notifier) -> None:
    """
    Set up global exception tracking.
    
    Args:
        notifier: Notification service for alerts
    """
    logger.info("Setting up exception tracking")
    
    # Create the exception tracker
    tracker = CustomExceptionTracker(notifier)
    
    # Set the global exception hook
    sys.excepthook = tracker.handle_exception
    
    logger.info("Exception tracking initialized successfully")
