#!/usr/bin/env python
"""
Main application for monitoring system for Xenorize and Cryptellar projects.
Provides health checks, exception tracking, API connectivity testing, 
performance monitoring, database monitoring, and Telegram notifications.
"""
import logging
import time
import schedule
import threading
import os
from pathlib import Path
from dotenv import load_dotenv

from monitoring.health_check import run_health_checks
from monitoring.exception_tracker import setup_exception_tracking
from monitoring.performance import check_system_performance
from monitoring.api_validator import run_api_validations
from monitoring.database_monitor import run_database_checks
from monitoring.bot_monitor import run_bot_monitoring
from monitoring.log_monitor import LogMonitoringManager, run_log_forwarding
from monitoring.uptime_monitor import run_uptime_checks
from monitoring.remote_access import check_remote_access_tools
from monitoring.exchange_api_monitor import run_exchange_api_checks, test_webhooks
from monitoring.database_monitor import run_database_checks
from monitoring.anomaly_detection import check_system_anomalies, check_api_anomalies
from monitoring.dynamic_monitor import run_dynamic_monitoring
from utils.dynamic_config_manager import DynamicConfigManager
from api.config_manager_api import app as config_api_app
from utils.config import Config
from utils.notification import TelegramNotifier

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("monitoring_service")

# Load environment variables
load_dotenv()

# Initialize configuration manager
config_manager = DynamicConfigManager()
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize config
config = Config()
notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)


def run_scheduled_job():
    """Run all monitoring jobs according to schedule"""
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_api_server(host="0.0.0.0", port=8000):
    """Start the API server for configuration management in a separate thread."""
    import uvicorn
    
    class Server(uvicorn.Server):
        def install_signal_handlers(self):
            # Override to prevent API server from capturing signals
            pass
    
    config = uvicorn.Config(config_api_app, host=host, port=port, log_level="info")
    server = Server(config=config)
    
    api_thread = threading.Thread(target=server.run)
    api_thread.daemon = True
    api_thread.start()
    
    logger.info(f"Started API server at http://{host}:{port}")
    return api_thread

def start_monitoring():
    """Setup and start all monitoring services"""
    logger.info("Starting monitoring services")
    
    # Setup global exception tracking
    setup_exception_tracking(notifier)
    
    # Initialize log monitoring
    log_manager = LogMonitoringManager(config)
    schedule.every(config.log_check_interval).seconds.do(
        run_log_forwarding,
        log_manager=log_manager,
        config=config,
        notifier=notifier
    )
    
    # Schedule uptime checks
    schedule.every(config.uptime_check_interval).seconds.do(
        run_uptime_checks,
        config=config,
        notifier=notifier
    )
    
    # Schedule remote access tools monitoring
    schedule.every(config.remote_access_check_interval).seconds.do(
        check_remote_access_tools,
        config=config,
        notifier=notifier
    )
    
    # Schedule exchange API monitoring
    schedule.every(config.exchange_api_check_interval).seconds.do(
        run_exchange_api_checks,
        config=config,
        notifier=notifier
    )
    
    # Schedule webhook testing (less frequent)
    schedule.every(config.webhook_test_interval).seconds.do(
        test_webhooks,
        config=config,
        notifier=notifier
    )
    
    # Schedule database monitoring
    schedule.every(config.database_check_interval).seconds.do(
        run_database_checks,
        config=config,
        notifier=notifier
    )
    
    # Schedule anomaly detection (less frequent)
    schedule.every(config.anomaly_detection_interval).seconds.do(
        check_system_anomalies,
        config=config,
        notifier=notifier
    )
    schedule.every(config.anomaly_detection_interval * 2).seconds.do(
        check_api_anomalies,
        config=config,
        notifier=notifier
    )
    
    # Start dynamic target monitoring if enabled
    if config.enable_dynamic_monitoring:
        try:
            dynamic_monitor = run_dynamic_monitoring(config, notifier)
            logger.info("Dynamic target monitoring started")
        except Exception as e:
            logger.error(f"Failed to start dynamic target monitoring: {e}")
            notifier.send_alert(f"⚠️ Failed to start dynamic target monitoring: {e}")
    
    # Schedule basic health checks
    schedule.every(config.check_interval).seconds.do(
        run_health_checks, 
        config=config,
        notifier=notifier
    )
    
    # Schedule performance monitoring
    schedule.every(config.check_interval).seconds.do(
        check_system_performance, 
        config=config,
        notifier=notifier
    )
    
    # Schedule comprehensive API validations (less frequent)
    schedule.every(config.api_validation_interval).seconds.do(
        run_api_validations,
        config=config,
        notifier=notifier
    )
    
    # Schedule database monitoring
    schedule.every(config.database_check_interval).seconds.do(
        run_database_checks,
        config=config,
        notifier=notifier
    )
    
    # Schedule bot process monitoring
    schedule.every(config.bot_check_interval).seconds.do(
        run_bot_monitoring,
        config=config,
        notifier=notifier
    )
    
    # Daily system status report
    schedule.every().day.at("08:00").do(
        send_daily_report,
        config=config,
        notifier=notifier
    )
    
    # Start the scheduling thread
    scheduler_thread = threading.Thread(target=run_scheduled_job, daemon=True)
    scheduler_thread.start()
    
    logger.info("Monitoring services started successfully")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(60)
            logger.debug("Monitoring service is running")
    except KeyboardInterrupt:
        logger.info("Monitoring service stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in monitoring service: {str(e)}")
        notifier.send_alert(f"🚨 CRITICAL: Monitoring service stopped due to error: {str(e)}")


def send_daily_report(config, notifier):
    """Send a daily status report with system health summary"""
    from monitoring.health_check import service_status
    from monitoring.performance import get_system_metrics
    
    logger.info("Generating daily status report")
    
    # Get current metrics
    metrics = get_system_metrics()
    
    # Generate report
    status_summary = []
    all_ok = True
    
    for service_name, info in service_status.items():
        if info["last_status"] != "ok":
            status_summary.append(f"❌ {service_name}: {info['failures']} consecutive failures")
            all_ok = False
        else:
            status_summary.append(f"✅ {service_name}: OK")
    
    # Format report
    if all_ok:
        emoji = "🟢"
        status_text = "ALL SYSTEMS OPERATIONAL"
    else:
        emoji = "🟠"
        status_text = "SYSTEM ISSUES DETECTED"
    
    report = (
        f"{emoji} DAILY STATUS REPORT: {status_text}\n\n"
        f"Service Status:\n" + "\n".join(status_summary) + "\n\n"
        f"System Performance:\n"
        f"- CPU: {metrics['cpu']['percent']}%\n"
        f"- Memory: {metrics['memory']['percent']}%\n"
        f"- Disk: {metrics['disk']['percent']}%\n\n"
        f"Monitoring service has been running for {metrics['system']['uptime'] / 3600:.1f} hours."
    )
    
    # Send the report
    notifier.send_alert(report)


if __name__ == "__main__":
    # Send startup notification
    notifier.send_alert("🟢 Monitoring service started!")
    
    # Start monitoring
    start_monitoring()
