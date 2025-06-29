"""
Database monitoring module to check database connectivity and performance.
Provides advanced monitoring for database connections, performance metrics,
replication status, and query analysis.
"""
import logging
import time
import json
import os
import datetime
from typing import Dict, Any, Optional, List, Tuple
import requests
import sqlite3
from collections import deque

logger = logging.getLogger("monitoring.database")

# Ensure data directory exists
os.makedirs("data/database", exist_ok=True)

class DatabaseMonitor:
    """Monitor database connections and performance for bot services."""
    
    def __init__(self, service_name: str, db_config: Dict[str, Any]):
        """
        Initialize database monitor.
        
        Args:
            service_name: Name of the service (xenorize or cryptellar)
            db_config: Database configuration details
        """
        self.service_name = service_name
        self.db_config = db_config
        self.history = deque(maxlen=100)  # Store last 100 check results
        self.last_alert_time = {}
        
        # Metrics history for trend analysis
        self.metrics_history = {
            "connection_time": deque(maxlen=50),
            "query_time": deque(maxlen=50),
            "active_connections": deque(maxlen=50),
            "deadlocks": deque(maxlen=50),
            "replication_lag": deque(maxlen=50)
        }
        
    def check_connection(self) -> Dict[str, Any]:
        """
        Check database connection status using API endpoint.
        
        Returns:
            Dictionary with connection status
        """
        try:
            # Use API endpoint that tests DB connection
            url = f"{self.db_config['api_url']}/system/database/status"
            headers = {"Authorization": f"Bearer {self.db_config['api_key']}"}
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "ok" if data.get("connected", False) else "error",
                    "response_time": response_time,
                    "service": f"{self.service_name}_database",
                    "details": data
                }
            else:
                return {
                    "status": "error",
                    "error": f"API returned {response.status_code}",
                    "service": f"{self.service_name}_database"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": f"{self.service_name}_database"
            }
    
    def check_performance(self) -> Dict[str, Any]:
        """
        Check database performance metrics using API endpoint.
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            url = f"{self.db_config['api_url']}/system/database/metrics"
            headers = {"Authorization": f"Bearer {self.db_config['api_key']}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                metrics = data.get("metrics", {})
                
                # Store metrics for trend analysis
                if "avg_query_time_ms" in metrics:
                    self.metrics_history["query_time"].append({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "value": metrics["avg_query_time_ms"]
                    })
                
                if "active_connections" in metrics:
                    self.metrics_history["active_connections"].append({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "value": metrics["active_connections"]
                    })
                    
                if "deadlocks" in metrics:
                    self.metrics_history["deadlocks"].append({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "value": metrics["deadlocks"]
                    })
                
                # Save metrics to disk
                self._save_metrics(metrics)
                
                return {
                    "status": "ok",
                    "service": f"{self.service_name}_database",
                    "metrics": metrics,
                    "trends": self._analyze_trends()
                }
            else:
                return {
                    "status": "error",
                    "error": f"API returned {response.status_code}",
                    "service": f"{self.service_name}_database"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": f"{self.service_name}_database"
            }


    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save metrics to disk for historical analysis."""
        try:
            timestamp = datetime.datetime.now().isoformat()
            metrics_file = f"data/database/{self.service_name}_metrics.json"
            
            # Load existing data if available
            data = []
            if os.path.exists(metrics_file):
                try:
                    with open(metrics_file, "r") as f:
                        data = json.load(f)
                except Exception:
                    # If file is corrupted, start fresh
                    data = []
            
            # Add new metrics with timestamp
            metrics["timestamp"] = timestamp
            data.append(metrics)
            
            # Keep only the last 1000 entries
            if len(data) > 1000:
                data = data[-1000:]
            
            # Write to file
            with open(metrics_file, "w") as f:
                json.dump(data, f)
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends in metrics data."""
        trends = {}
        
        # Analyze query time trend
        if len(self.metrics_history["query_time"]) > 5:
            values = [item["value"] for item in self.metrics_history["query_time"]]
            trends["query_time"] = {
                "current": values[-1],
                "avg_5": sum(values[-5:]) / 5,
                "min": min(values),
                "max": max(values),
                "trend": "increasing" if values[-1] > values[-5] else "decreasing"
            }
        
        # Analyze active connections trend
        if len(self.metrics_history["active_connections"]) > 5:
            values = [item["value"] for item in self.metrics_history["active_connections"]]
            trends["active_connections"] = {
                "current": values[-1],
                "avg_5": sum(values[-5:]) / 5,
                "min": min(values),
                "max": max(values),
                "trend": "increasing" if values[-1] > values[-5] else "decreasing"
            }
        
        # Analyze deadlocks trend
        if len(self.metrics_history["deadlocks"]) > 5:
            values = [item["value"] for item in self.metrics_history["deadlocks"]]
            trends["deadlocks"] = {
                "current": values[-1],
                "total": sum(values)
            }
        
        return trends
    
    def check_replication_status(self) -> Dict[str, Any]:
        """Check database replication status if applicable."""
        try:
            # Only proceed if replication endpoint is configured
            if not self.db_config.get("check_replication", False):
                return {"status": "not_applicable", "message": "Replication monitoring not enabled"}
            
            url = f"{self.db_config['api_url']}/system/database/replication"
            headers = {"Authorization": f"Bearer {self.db_config['api_key']}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Store replication lag in history
                if "lag_seconds" in data:
                    self.metrics_history["replication_lag"].append({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "value": data["lag_seconds"]
                    })
                
                return {
                    "status": "ok" if data.get("healthy", False) else "degraded",
                    "service": f"{self.service_name}_database_replication",
                    "replication": data
                }
            else:
                return {
                    "status": "error",
                    "error": f"API returned {response.status_code}",
                    "service": f"{self.service_name}_database_replication"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": f"{self.service_name}_database_replication"
            }
    
    def analyze_slow_queries(self) -> Dict[str, Any]:
        """Analyze slow queries report from database."""
        try:
            url = f"{self.db_config['api_url']}/system/database/slow-queries"
            headers = {"Authorization": f"Bearer {self.db_config['api_key']}"}
            
            response = requests.get(url, headers=headers, timeout=15)  # Longer timeout for slow query analysis
            
            if response.status_code == 200:
                data = response.json()
                slow_queries = data.get("slow_queries", [])
                
                # Save to disk for historical reference
                if slow_queries:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    with open(f"data/database/{self.service_name}_slow_queries_{timestamp}.json", "w") as f:
                        json.dump(slow_queries, f)
                
                return {
                    "status": "warning" if slow_queries else "ok",
                    "service": f"{self.service_name}_database_queries",
                    "slow_queries_count": len(slow_queries),
                    "slow_queries": slow_queries[:5]  # Return only 5 worst queries to avoid large payloads
                }
            else:
                return {
                    "status": "error",
                    "error": f"API returned {response.status_code}",
                    "service": f"{self.service_name}_database_queries"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": f"{self.service_name}_database_queries"
            }
    
    def check_connections_pool(self) -> Dict[str, Any]:
        """Check database connection pool status."""
        try:
            url = f"{self.db_config['api_url']}/system/database/connections"
            headers = {"Authorization": f"Bearer {self.db_config['api_key']}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pool_data = data.get("pool", {})
                
                # Calculate utilization percentage
                if "max_connections" in pool_data and "active_connections" in pool_data:
                    utilization = (pool_data["active_connections"] / pool_data["max_connections"]) * 100
                    pool_data["utilization_percent"] = round(utilization, 2)
                
                return {
                    "status": "warning" if utilization > 80 else "ok",
                    "service": f"{self.service_name}_database_pool",
                    "pool": pool_data
                }
            else:
                return {
                    "status": "error",
                    "error": f"API returned {response.status_code}",
                    "service": f"{self.service_name}_database_pool"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "service": f"{self.service_name}_database_pool"
            }


def run_database_checks(config, notifier) -> None:
    """
    Run comprehensive database checks for all configured services.
    Includes connection status, performance metrics, replication status,
    connection pool health, and slow query analysis.
    
    Args:
        config: Application configuration
        notifier: Notification service
        
    Returns:
        None
    """
    logger.info("Running comprehensive database checks")
    results = {"xenorize": {}, "cryptellar": {}}
    
    # Run database checks for each configured platform
    platforms = [("xenorize", config.xenorize_api_url, config.xenorize_api_key),
                ("cryptellar", config.cryptellar_api_url, config.cryptellar_api_key)]
    
    for platform, api_url, api_key in platforms:
        if not api_url or not api_key:
            logger.info(f"Skipping {platform} database checks - not configured")
            continue
            
        logger.info(f"Running {platform} database checks")
        
        # Initialize database config with replication check flag
        db_config = {
            "api_url": api_url,
            "api_key": api_key,
            "check_replication": getattr(config, f"{platform}_check_replication", False)
        }
        
        # Create monitor
        monitor = DatabaseMonitor(platform, db_config)
        platform_results = {}
        
        # 1. Check basic connection
        connection_result = monitor.check_connection()
        platform_results["connection"] = connection_result
        
        # Skip further checks if connection fails
        if connection_result["status"] != "ok":
            logger.warning(f"{platform.capitalize()} database connection check failed: {connection_result.get('error', 'Unknown error')}")
            notifier.send_alert(
                f"🚨 DATABASE CONNECTION ISSUE: {platform.upper()}\n\n"
                f"Error: {connection_result.get('error', 'Unknown error')}",
                priority="high"
            )
            results[platform] = platform_results
            continue
        
        # 2. Check performance metrics
        performance_result = monitor.check_performance()
        platform_results["performance"] = performance_result
        metrics = performance_result.get("metrics", {})
        
        # Alert on concerning performance metrics
        concerns = []
        if metrics.get("avg_query_time_ms", 0) > 500:  # Average query time > 500ms
            concerns.append(f"Slow query time: {metrics.get('avg_query_time_ms')}ms")
        
        if metrics.get("active_connections", 0) > metrics.get("max_connections", 100) * 0.8:  # Over 80% connections used
            concerns.append(f"High connection usage: {metrics.get('active_connections')} of {metrics.get('max_connections')}")
            
        if metrics.get("deadlocks", 0) > 0:  # Any deadlocks
            concerns.append(f"Deadlocks detected: {metrics.get('deadlocks')}")
            
        if concerns:
            logger.warning(f"{platform.capitalize()} database performance issues: {', '.join(concerns)}")
            notifier.send_alert(
                f"⚠️ DATABASE PERFORMANCE WARNING: {platform.upper()}\n\n"
                f"Issues detected:\n- " + "\n- ".join(concerns) + "\n\n"
                f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                priority="normal"
            )
        
        # 3. Check replication status if enabled
        if getattr(config, f"{platform}_check_replication", False):
            replication_result = monitor.check_replication_status()
            platform_results["replication"] = replication_result
            
            # Alert on replication issues
            if replication_result.get("status") not in ["ok", "not_applicable"]:
                replication_data = replication_result.get("replication", {})
                lag_seconds = replication_data.get("lag_seconds", 0)
                
                # Determine severity based on lag
                priority = "normal"
                if lag_seconds > 300:  # 5 minutes lag
                    priority = "high"
                
                logger.warning(f"{platform.capitalize()} database replication issue: {replication_result.get('error') or f'Lag of {lag_seconds} seconds'}")
                notifier.send_alert(
                    f"⚠️ DATABASE REPLICATION ISSUE: {platform.upper()}\n\n"
                    f"Status: {replication_result.get('status')}\n"
                    f"Lag: {lag_seconds} seconds\n"
                    f"Primary server: {replication_data.get('primary_server', 'Unknown')}\n"
                    f"Replica server: {replication_data.get('replica_server', 'Unknown')}",
                    priority=priority
                )
        
        # 4. Check connection pool status
        pool_result = monitor.check_connections_pool()
        platform_results["connection_pool"] = pool_result
        
        # Alert on high pool utilization
        if pool_result.get("status") == "warning":
            pool_data = pool_result.get("pool", {})
            logger.warning(f"{platform.capitalize()} database connection pool near capacity: {pool_data.get('utilization_percent', 0)}% used")
            notifier.send_alert(
                f"⚠️ DATABASE CONNECTION POOL WARNING: {platform.upper()}\n\n"
                f"Utilization: {pool_data.get('utilization_percent', 0)}%\n"
                f"Active connections: {pool_data.get('active_connections', 0)} of {pool_data.get('max_connections', 0)}",
                priority="normal"
            )
        
        # 5. Check for slow queries (less frequently)
        if datetime.datetime.now().minute % 10 == 0:  # Run every 10 minutes
            query_result = monitor.analyze_slow_queries()
            platform_results["slow_queries"] = query_result
            
            if query_result.get("status") == "warning" and query_result.get("slow_queries_count", 0) > 0:
                slow_queries = query_result.get("slow_queries", [])
                slow_query_count = query_result.get("slow_queries_count", 0)
                
                # Format slow query information
                query_details = ""
                for i, query in enumerate(slow_queries[:3]):  # Show top 3
                    query_details += f"\n#{i+1}: {query.get('query_text', '')[:100]}...\n"
                    query_details += f"   Execution time: {query.get('execution_time_ms', 0)}ms\n"
                    query_details += f"   Tables: {', '.join(query.get('tables', ['Unknown']))}\n"
                
                logger.warning(f"{platform.capitalize()} database has {slow_query_count} slow queries")
                notifier.send_alert(
                    f"⚠️ SLOW DATABASE QUERIES DETECTED: {platform.upper()}\n\n"
                    f"Total slow queries: {slow_query_count}\n\n"
                    f"Top offenders:{query_details}",
                    priority="normal"
                )
        
        # Save all results
        results[platform] = platform_results
    
    # Save comprehensive results to disk
    try:
        results["timestamp"] = datetime.datetime.now().isoformat()
        with open("data/database/latest_check_results.json", "w") as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving database check results: {e}")
    
    return results
