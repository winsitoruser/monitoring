"""
Configuration module for the monitoring system.
Loads and provides access to environment variables and application settings.
"""
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("utils.config")


class Config:
    """
    Configuration class for the monitoring system.
    Loads configuration from environment variables.
    """
    
    def __init__(self):
        """Initialize the configuration from environment variables."""
        # Telegram configuration
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        # Basic monitoring configuration
        try:
            self.check_interval = int(os.getenv("CHECK_INTERVAL", "300"))
        except ValueError:
            self.check_interval = 300
            logger.warning("Invalid CHECK_INTERVAL value, defaulting to 300 seconds")
            
        try:
            self.alert_threshold = int(os.getenv("ALERT_THRESHOLD", "3"))
        except ValueError:
            self.alert_threshold = 3
            logger.warning("Invalid ALERT_THRESHOLD value, defaulting to 3")
        
        # Advanced monitoring intervals
        try:
            # API validation runs less frequently than basic health checks
            self.api_validation_interval = int(os.getenv("API_VALIDATION_INTERVAL", "900"))  # 15 minutes default
        except ValueError:
            self.api_validation_interval = 900
            logger.warning("Invalid API_VALIDATION_INTERVAL value, defaulting to 900 seconds")
            
        try:
            # Database check interval
            self.database_check_interval = int(os.getenv("DATABASE_CHECK_INTERVAL", "600"))  # 10 minutes default
        except ValueError:
            self.database_check_interval = 600
            logger.warning("Invalid DATABASE_CHECK_INTERVAL value, defaulting to 600 seconds")
            
        try:
            # Anomaly detection interval
            self.anomaly_detection_interval = int(os.getenv("ANOMALY_DETECTION_INTERVAL", "1800"))  # 30 minutes default
        except ValueError:
            self.anomaly_detection_interval = 1800
            logger.warning("Invalid ANOMALY_DETECTION_INTERVAL value, defaulting to 1800 seconds")
            
        # Advanced notification settings
        self.enable_slack_notifications = os.getenv("ENABLE_SLACK_NOTIFICATIONS", "false").lower() == "true"
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.slack_channel = os.getenv("SLACK_CHANNEL", "#alerts")
        
        self.enable_email_notifications = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "false").lower() == "true"
        self.email_smtp_server = os.getenv("EMAIL_SMTP_SERVER", "")
        self.email_smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.email_smtp_username = os.getenv("EMAIL_SMTP_USERNAME", "")
        self.email_smtp_password = os.getenv("EMAIL_SMTP_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM", "")
        self.email_recipients = os.getenv("EMAIL_RECIPIENTS", "").split(",")
        
        self.enable_sms_notifications = os.getenv("ENABLE_SMS_NOTIFICATIONS", "false").lower() == "true"
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER", "")
        self.twilio_to_numbers = os.getenv("TWILIO_TO_NUMBERS", "").split(",")
        
        # Dynamic Configuration Manager settings
        self.enable_dynamic_monitoring = os.getenv("ENABLE_DYNAMIC_MONITORING", "true").lower() == "true"
        self.enable_config_api = os.getenv("ENABLE_CONFIG_API", "true").lower() == "true"
        self.config_api_host = os.getenv("CONFIG_API_HOST", "127.0.0.1")
        
        try:
            self.config_api_port = int(os.getenv("CONFIG_API_PORT", "8080"))
        except ValueError:
            self.config_api_port = 8080
            logger.warning("Invalid CONFIG_API_PORT value, defaulting to 8080")
            
        self.config_api_key = os.getenv("CONFIG_API_KEY", "")  # Security key for API access
            
        try:
            # Bot process monitoring interval
            self.bot_check_interval = int(os.getenv("BOT_CHECK_INTERVAL", "120"))  # 2 minutes default
        except ValueError:
            self.bot_check_interval = 120
            logger.warning("Invalid BOT_CHECK_INTERVAL value, defaulting to 120 seconds")
            
        try:
            # Log monitoring interval
            self.log_check_interval = int(os.getenv("LOG_CHECK_INTERVAL", "300"))  # 5 minutes default
        except ValueError:
            self.log_check_interval = 300
            logger.warning("Invalid LOG_CHECK_INTERVAL value, defaulting to 300 seconds")
            
        try:
            # Uptime monitoring interval
            self.uptime_check_interval = int(os.getenv("UPTIME_CHECK_INTERVAL", "60"))  # 1 minute default
        except ValueError:
            self.uptime_check_interval = 60
            logger.warning("Invalid UPTIME_CHECK_INTERVAL value, defaulting to 60 seconds")
            
        try:
            # Remote access tools monitoring interval
            self.remote_access_check_interval = int(os.getenv("REMOTE_ACCESS_CHECK_INTERVAL", "1800"))  # 30 minutes default
        except ValueError:
            self.remote_access_check_interval = 1800
            logger.warning("Invalid REMOTE_ACCESS_CHECK_INTERVAL value, defaulting to 1800 seconds")
            
        # Performance thresholds
        try:
            self.performance_warning_cpu = int(os.getenv("PERFORMANCE_WARNING_CPU", "80"))
        except ValueError:
            self.performance_warning_cpu = 80
            logger.warning("Invalid PERFORMANCE_WARNING_CPU value, defaulting to 80%")
            
        try:
            self.performance_warning_memory = int(os.getenv("PERFORMANCE_WARNING_MEMORY", "80"))
        except ValueError:
            self.performance_warning_memory = 80
            logger.warning("Invalid PERFORMANCE_WARNING_MEMORY value, defaulting to 80%")
        
        # API configuration
        self.xenorize_api_url = os.getenv("XENORIZE_API_URL", "")
        self.xenorize_api_key = os.getenv("XENORIZE_API_KEY", "")
        self.cryptellar_api_url = os.getenv("CRYPTELLAR_API_URL", "")
        self.cryptellar_api_key = os.getenv("CRYPTELLAR_API_KEY", "")
        
        # Database monitoring configuration
        self.xenorize_check_replication = os.getenv("XENORIZE_CHECK_REPLICATION", "false").lower() == "true"
        self.cryptellar_check_replication = os.getenv("CRYPTELLAR_CHECK_REPLICATION", "false").lower() == "true"
        
        # Database monitoring thresholds
        try:
            self.db_query_time_threshold = int(os.getenv("DB_QUERY_TIME_THRESHOLD", "500"))  # milliseconds
        except ValueError:
            self.db_query_time_threshold = 500
            
        try:
            self.db_connection_threshold = float(os.getenv("DB_CONNECTION_THRESHOLD", "0.8"))  # 80% of max connections
        except ValueError:
            self.db_connection_threshold = 0.8
            
        try:
            self.db_replication_lag_threshold = int(os.getenv("DB_REPLICATION_LAG_THRESHOLD", "300"))  # seconds
        except ValueError:
            self.db_replication_lag_threshold = 300
        
        # Bot process monitoring configuration
        # Bot process settings
        self.xenorize_bot_process = os.getenv("XENORIZE_BOT_PROCESS", "xenorize_bot")
        self.xenorize_bot_start_command = os.getenv("XENORIZE_BOT_START_COMMAND")
        self.xenorize_bot_directory = os.getenv("XENORIZE_BOT_DIRECTORY", ".")
        
        self.cryptellar_bot_process = os.getenv("CRYPTELLAR_BOT_PROCESS", "cryptellar_bot")
        self.cryptellar_bot_start_command = os.getenv("CRYPTELLAR_BOT_START_COMMAND")
        self.cryptellar_bot_directory = os.getenv("CRYPTELLAR_BOT_DIRECTORY", ".")
        
        # Log monitoring settings
        self.app_name = os.getenv("APP_NAME", "monitoring-service")
        self.log_directory = os.getenv("LOG_DIRECTORY", "logs")
        
        # ELK Stack integration
        self.elasticsearch_enabled = os.getenv("LOG_MONITOR_ELASTICSEARCH_ENABLED", "false").lower() == "true"
        self.elasticsearch_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.elasticsearch_index = os.getenv("ELASTICSEARCH_INDEX", "monitoring-logs")
        self.elasticsearch_user = os.getenv("ELASTICSEARCH_USER")
        self.elasticsearch_password = os.getenv("ELASTICSEARCH_PASSWORD")
        
        # Graylog integration
        self.graylog_enabled = os.getenv("LOG_MONITOR_GRAYLOG_ENABLED", "false").lower() == "true"
        self.graylog_url = os.getenv("GRAYLOG_URL", "localhost")
        self.graylog_port = int(os.getenv("GRAYLOG_PORT", "12201"))
        self.graylog_use_https = os.getenv("GRAYLOG_USE_HTTPS", "false").lower() == "true"
        
        # Papertrail integration
        self.papertrail_enabled = os.getenv("LOG_MONITOR_PAPERTRAIL_ENABLED", "false").lower() == "true"
        self.papertrail_host = os.getenv("PAPERTRAIL_HOST", "logs.papertrailapp.com")
        self.papertrail_port = int(os.getenv("PAPERTRAIL_PORT", "12345"))
        
        # Fluentd integration
        self.fluentd_enabled = os.getenv("LOG_MONITOR_FLUENTD_ENABLED", "false").lower() == "true"
        self.fluentd_url = os.getenv("FLUENTD_URL", "http://localhost:24224")
        self.fluentd_tag = os.getenv("FLUENTD_TAG", "monitoring")
        
        # Uptime monitoring external services
        self.uptimerobot_api_key = os.getenv("UPTIMEROBOT_API_KEY")
        self.pingdom_api_key = os.getenv("PINGDOM_API_KEY")
        self.statuscake_api_key = os.getenv("STATUSCAKE_API_KEY")
        self.statuscake_username = os.getenv("STATUSCAKE_USERNAME")
        
        # Remote access tools configuration
        self.enable_ssh_monitoring = os.getenv("ENABLE_SSH_MONITORING", "true").lower() == "true"
        
        # VPN monitoring
        vpn_types = os.getenv("MONITORED_VPN_TYPES", "openvpn,wireguard,tailscale")
        self.monitored_vpn_types = [vpn.strip() for vpn in vpn_types.split(",") if vpn.strip()]
        
        # Remote desktop tools
        desktop_tools = os.getenv("MONITORED_DESKTOP_TOOLS", "anydesk,teamviewer")
        self.monitored_desktop_tools = [tool.strip() for tool in desktop_tools.split(",") if tool.strip()]
        
        # Docker management
        self.enable_docker_monitoring = os.getenv("ENABLE_DOCKER_MONITORING", "true").lower() == "true"
        self.enable_portainer_monitoring = os.getenv("ENABLE_PORTAINER_MONITORING", "false").lower() == "true"
        self.portainer_url = os.getenv("PORTAINER_URL", "http://localhost:9000")
        self.enable_rancher_monitoring = os.getenv("ENABLE_RANCHER_MONITORING", "false").lower() == "true"
        self.rancher_url = os.getenv("RANCHER_URL", "http://localhost:8080")
        
        # Exchange API monitoring configuration
        exchanges_str = os.getenv("MONITORED_EXCHANGES", "binance,coinbase")
        self.monitored_exchanges = [ex.strip() for ex in exchanges_str.split(",") if ex.strip()]
        
        # Exchange API credentials and endpoints
        for exchange in self.monitored_exchanges:
            # API key and secret
            api_key_var = f"{exchange.upper()}_API_KEY"
            api_secret_var = f"{exchange.upper()}_API_SECRET"
            api_url_var = f"{exchange.upper()}_API_URL"
            endpoints_var = f"{exchange.upper()}_ENDPOINTS"
            
            setattr(self, f"{exchange.lower()}_api_key", os.getenv(api_key_var, ""))
            setattr(self, f"{exchange.lower()}_api_secret", os.getenv(api_secret_var, ""))
            setattr(self, f"{exchange.lower()}_api_url", os.getenv(api_url_var, ""))
            setattr(self, f"{exchange.lower()}_endpoints", os.getenv(endpoints_var, ""))
        
        # Webhook monitoring configuration
        webhooks_str = os.getenv("MONITORED_WEBHOOKS", "xenorize,cryptellar")
        self.monitored_webhooks = [wh.strip() for wh in webhooks_str.split(",") if wh.strip()]
        
        # Webhook configurations
        for webhook in self.monitored_webhooks:
            webhook_url_var = f"{webhook.upper()}_WEBHOOK_URL"
            webhook_secret_var = f"{webhook.upper()}_WEBHOOK_SECRET"
            webhook_test_payload_var = f"{webhook.upper()}_WEBHOOK_TEST_PAYLOAD"
            
            setattr(self, f"{webhook.lower()}_webhook_url", os.getenv(webhook_url_var, ""))
            setattr(self, f"{webhook.lower()}_webhook_secret", os.getenv(webhook_secret_var, ""))
            setattr(self, f"{webhook.lower()}_webhook_test_payload", os.getenv(webhook_test_payload_var, "{}"))
            
        # Exchange API check interval
        try:
            self.exchange_api_check_interval = int(os.getenv("EXCHANGE_API_CHECK_INTERVAL", "300"))  # 5 minutes default
        except ValueError:
            self.exchange_api_check_interval = 300
            logger.warning("Invalid EXCHANGE_API_CHECK_INTERVAL value, defaulting to 300 seconds")
            
        # Webhook test interval
        try:
            self.webhook_test_interval = int(os.getenv("WEBHOOK_TEST_INTERVAL", "3600"))  # 1 hour default
        except ValueError:
            self.webhook_test_interval = 3600
            logger.warning("Invalid WEBHOOK_TEST_INTERVAL value, defaulting to 3600 seconds")
        
        # Validate required configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        Validate that all required configuration is present.
        Logs warnings for missing configuration.
        """
        if not self.telegram_bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Notifications will not be sent.")
            
        if not self.telegram_chat_id:
            logger.warning("TELEGRAM_CHAT_ID not set. Notifications will not be sent.")
            
        if not self.xenorize_api_url:
            logger.warning("XENORIZE_API_URL not set. Xenorize API monitoring will be disabled.")
            
        if not self.xenorize_api_key:
            logger.warning("XENORIZE_API_KEY not set. Xenorize API monitoring will be disabled.")
            
        if not self.cryptellar_api_url:
            logger.warning("CRYPTELLAR_API_URL not set. Cryptellar API monitoring will be disabled.")
            
        if not self.cryptellar_api_key:
            logger.warning("CRYPTELLAR_API_KEY not set. Cryptellar API monitoring will be disabled.")
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Return configuration as a dictionary.
        Masks sensitive values like API keys.
        
        Returns:
            Dictionary of configuration values
        """
        return {
            "check_interval": self.check_interval,
            "alert_threshold": self.alert_threshold,
            "performance_warning_cpu": self.performance_warning_cpu,
            "performance_warning_memory": self.performance_warning_memory,
            "telegram_configured": bool(self.telegram_bot_token and self.telegram_chat_id),
            "xenorize_api_configured": bool(self.xenorize_api_url and self.xenorize_api_key),
            "cryptellar_api_configured": bool(self.cryptellar_api_url and self.cryptellar_api_key),
        }
