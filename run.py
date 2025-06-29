#!/usr/bin/env python
"""
Combined runner script that launches both the monitoring service and dashboard.
This is the main entry point for Docker deployments.
"""
import logging
import threading
import time
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("monitor_runner")

def start_monitoring_service():
    """Start the main monitoring service in a separate thread."""
    logger.info("Starting monitoring service...")
    from main import start_monitoring
    monitoring_thread = threading.Thread(target=start_monitoring, daemon=True)
    monitoring_thread.start()
    return monitoring_thread

def start_dashboard_service():
    """Start the dashboard service in a separate thread."""
    logger.info("Starting dashboard service...")
    from dashboard import start_dashboard
    dashboard_thread = start_dashboard(host="0.0.0.0", port=8080)
    return dashboard_thread

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Load environment variables
    from dotenv import load_dotenv
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Start monitoring service
    monitoring_thread = start_monitoring_service()
    
    # Give the monitoring service time to initialize
    time.sleep(2)
    
    # Start dashboard service
    dashboard_thread = start_dashboard_service()
    
    logger.info("All services started. Press Ctrl+C to exit.")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(10)
            if not monitoring_thread.is_alive():
                logger.error("Monitoring service has died! Attempting restart...")
                monitoring_thread = start_monitoring_service()
                
            if not dashboard_thread.is_alive():
                logger.error("Dashboard service has died! Attempting restart...")
                dashboard_thread = start_dashboard_service()
    except KeyboardInterrupt:
        logger.info("Shutting down services...")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
