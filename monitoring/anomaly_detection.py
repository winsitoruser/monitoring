"""
Anomaly detection module for monitoring metrics.
Detects unusual patterns in monitoring data using statistical methods.
"""

import logging
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import time

logger = logging.getLogger("monitoring.anomaly_detection")

class AnomalyDetector:
    """Detect anomalies in monitoring metrics using statistical methods."""
    
    def __init__(self, config):
        """
        Initialize the anomaly detector.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.metrics_history = {}
        self.anomalies_detected = {}
        
        # Create data directory
        os.makedirs("data/anomalies", exist_ok=True)
        
        # Load historical data if available
        self._load_metrics_history()
    
    def _load_metrics_history(self):
        """Load metrics history from disk if available."""
        try:
            if os.path.exists("data/metrics_history.json"):
                with open("data/metrics_history.json", "r") as f:
                    self.metrics_history = json.load(f)
                logger.info("Loaded metrics history from disk")
        except Exception as e:
            logger.error(f"Failed to load metrics history: {e}")
    
    def _save_metrics_history(self):
        """Save metrics history to disk."""
        try:
            with open("data/metrics_history.json", "w") as f:
                json.dump(self.metrics_history, f)
        except Exception as e:
            logger.error(f"Failed to save metrics history: {e}")
    
    def add_metric(self, name: str, value: float, category: str, timestamp: str = None):
        """
        Add a metric value to the history.
        
        Args:
            name: Metric name
            value: Metric value
            category: Metric category (e.g., 'api', 'performance', 'system')
            timestamp: Optional timestamp (ISO format)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # Initialize category and metric if not exist
        if category not in self.metrics_history:
            self.metrics_history[category] = {}
        
        if name not in self.metrics_history[category]:
            self.metrics_history[category][name] = []
        
        # Add the new data point
        self.metrics_history[category][name].append({
            "value": value,
            "timestamp": timestamp
        })
        
        # Trim history if too large (keep last 1000 points)
        if len(self.metrics_history[category][name]) > 1000:
            self.metrics_history[category][name] = self.metrics_history[category][name][-1000:]
        
        # Save metrics periodically (every 100 additions)
        if sum(len(metrics) for cat in self.metrics_history.values() 
               for metrics in cat.values()) % 100 == 0:
            self._save_metrics_history()
    
    def detect_anomalies_zscore(self, category: str, name: str, 
                               threshold: float = 3.0) -> Dict[str, Any]:
        """
        Detect anomalies using Z-score method.
        
        Args:
            category: Metric category
            name: Metric name
            threshold: Z-score threshold (default: 3.0)
            
        Returns:
            Dictionary with anomaly detection results
        """
        if category not in self.metrics_history or name not in self.metrics_history[category]:
            return {
                "status": "error",
                "message": f"No history for metric {category}.{name}"
            }
        
        # Get values from history
        history = self.metrics_history[category][name]
        if len(history) < 10:  # Need enough data points
            return {
                "status": "insufficient_data",
                "message": f"Need at least 10 data points, have {len(history)}"
            }
        
        values = np.array([point["value"] for point in history])
        
        # Calculate statistics
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:  # Avoid division by zero
            return {
                "status": "error",
                "message": "Standard deviation is zero, cannot compute Z-scores"
            }
        
        # Get the latest value
        latest_value = values[-1]
        latest_timestamp = history[-1]["timestamp"]
        
        # Calculate Z-score
        z_score = abs((latest_value - mean) / std)
        
        # Check if anomalous
        is_anomaly = z_score > threshold
        
        result = {
            "metric": f"{category}.{name}",
            "latest_value": latest_value,
            "latest_timestamp": latest_timestamp,
            "mean": float(mean),
            "std": float(std),
            "z_score": float(z_score),
            "threshold": threshold,
            "is_anomaly": is_anomaly
        }
        
        # Record anomaly if detected
        if is_anomaly:
            if category not in self.anomalies_detected:
                self.anomalies_detected[category] = {}
            
            if name not in self.anomalies_detected[category]:
                self.anomalies_detected[category][name] = []
            
            self.anomalies_detected[category][name].append({
                "value": latest_value,
                "timestamp": latest_timestamp,
                "z_score": float(z_score),
                "mean": float(mean),
                "std": float(std)
            })
            
            # Save anomaly to disk
            try:
                anomaly_file = f"data/anomalies/{category}_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(anomaly_file, "w") as f:
                    json.dump(result, f)
            except Exception as e:
                logger.error(f"Failed to save anomaly: {e}")
        
        return result
    
    def detect_outliers_iqr(self, category: str, name: str,
                           iqr_factor: float = 1.5) -> Dict[str, Any]:
        """
        Detect outliers using IQR method.
        
        Args:
            category: Metric category
            name: Metric name
            iqr_factor: IQR factor for outlier detection (default: 1.5)
            
        Returns:
            Dictionary with outlier detection results
        """
        if category not in self.metrics_history or name not in self.metrics_history[category]:
            return {
                "status": "error",
                "message": f"No history for metric {category}.{name}"
            }
        
        # Get values from history
        history = self.metrics_history[category][name]
        if len(history) < 10:  # Need enough data points
            return {
                "status": "insufficient_data",
                "message": f"Need at least 10 data points, have {len(history)}"
            }
        
        values = np.array([point["value"] for point in history])
        
        # Calculate quartiles
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        # Calculate bounds
        lower_bound = q1 - (iqr_factor * iqr)
        upper_bound = q3 + (iqr_factor * iqr)
        
        # Get the latest value
        latest_value = values[-1]
        latest_timestamp = history[-1]["timestamp"]
        
        # Check if outlier
        is_outlier = latest_value < lower_bound or latest_value > upper_bound
        
        result = {
            "metric": f"{category}.{name}",
            "latest_value": latest_value,
            "latest_timestamp": latest_timestamp,
            "q1": float(q1),
            "q3": float(q3),
            "iqr": float(iqr),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "iqr_factor": iqr_factor,
            "is_outlier": is_outlier
        }
        
        # Record anomaly if detected
        if is_outlier:
            if category not in self.anomalies_detected:
                self.anomalies_detected[category] = {}
            
            if name not in self.anomalies_detected[category]:
                self.anomalies_detected[category][name] = []
            
            self.anomalies_detected[category][name].append({
                "value": latest_value,
                "timestamp": latest_timestamp,
                "type": "iqr_outlier",
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound)
            })
            
            # Save anomaly to disk
            try:
                anomaly_file = f"data/anomalies/{category}_{name}_iqr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(anomaly_file, "w") as f:
                    json.dump(result, f)
            except Exception as e:
                logger.error(f"Failed to save outlier: {e}")
        
        return result
    
    def detect_trend(self, category: str, name: str, 
                    window_size: int = 10) -> Dict[str, Any]:
        """
        Detect trends in metric values.
        
        Args:
            category: Metric category
            name: Metric name
            window_size: Number of recent points to analyze
            
        Returns:
            Dictionary with trend detection results
        """
        if category not in self.metrics_history or name not in self.metrics_history[category]:
            return {
                "status": "error",
                "message": f"No history for metric {category}.{name}"
            }
        
        # Get values from history
        history = self.metrics_history[category][name]
        if len(history) < window_size:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {window_size} data points, have {len(history)}"
            }
        
        # Get the recent window of values
        recent_values = [point["value"] for point in history[-window_size:]]
        
        # Simple linear trend detection
        x = np.arange(window_size)
        y = np.array(recent_values)
        
        # Fit line to the data
        try:
            slope, intercept = np.polyfit(x, y, 1)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error fitting trend line: {e}"
            }
        
        # Calculate trend strength
        y_pred = intercept + slope * x
        r_squared = 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2))
        
        # Determine trend direction
        if abs(slope) < 0.001 or r_squared < 0.5:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
        
        return {
            "metric": f"{category}.{name}",
            "trend": trend,
            "slope": float(slope),
            "r_squared": float(r_squared),
            "window_size": window_size,
            "recent_values": recent_values
        }


def check_system_anomalies(config, notifier=None) -> Dict[str, Any]:
    """
    Check for anomalies in system metrics.
    
    Args:
        config: Application configuration
        notifier: Optional notification service
        
    Returns:
        Dictionary with anomaly detection results
    """
    logger.info("Checking for system anomalies")
    
    detector = AnomalyDetector(config)
    results = {
        "anomalies": [],
        "outliers": [],
        "trends": []
    }
    
    # Check CPU usage anomalies
    try:
        import psutil
        
        # Get current system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        # Add metrics to history
        detector.add_metric("cpu_usage", cpu_percent, "system")
        detector.add_metric("memory_usage", memory_percent, "system")
        detector.add_metric("disk_usage", disk_percent, "system")
        
        # Check for anomalies
        cpu_anomaly = detector.detect_anomalies_zscore("system", "cpu_usage")
        memory_anomaly = detector.detect_anomalies_zscore("system", "memory_usage")
        disk_anomaly = detector.detect_anomalies_zscore("system", "disk_usage")
        
        # Check for outliers
        cpu_outlier = detector.detect_outliers_iqr("system", "cpu_usage")
        memory_outlier = detector.detect_outliers_iqr("system", "memory_usage")
        disk_outlier = detector.detect_outliers_iqr("system", "disk_usage")
        
        # Check for trends
        cpu_trend = detector.detect_trend("system", "cpu_usage")
        memory_trend = detector.detect_trend("system", "memory_usage")
        disk_trend = detector.detect_trend("system", "disk_usage")
        
        # Collect results
        for result in [cpu_anomaly, memory_anomaly, disk_anomaly]:
            if "is_anomaly" in result and result["is_anomaly"]:
                results["anomalies"].append(result)
        
        for result in [cpu_outlier, memory_outlier, disk_outlier]:
            if "is_outlier" in result and result["is_outlier"]:
                results["outliers"].append(result)
        
        for result in [cpu_trend, memory_trend, disk_trend]:
            if "trend" in result and result["trend"] != "stable":
                results["trends"].append(result)
        
        # Send notifications if anomalies detected and notifier available
        if notifier and (results["anomalies"] or results["outliers"]):
            anomaly_messages = []
            
            for anomaly in results["anomalies"]:
                metric = anomaly["metric"]
                value = anomaly["latest_value"]
                message = f"{metric}: {value:.2f} (Z-score: {anomaly['z_score']:.2f})"
                anomaly_messages.append(message)
            
            for outlier in results["outliers"]:
                metric = outlier["metric"]
                value = outlier["latest_value"]
                message = f"{metric}: {value:.2f} (Outside IQR bounds: {outlier['lower_bound']:.2f}-{outlier['upper_bound']:.2f})"
                anomaly_messages.append(message)
            
            if anomaly_messages:
                notifier.send_alert(
                    "⚠️ ANOMALY DETECTION ALERT\n\n" +
                    "The following metrics show anomalous behavior:\n\n" +
                    "- " + "\n- ".join(anomaly_messages) + "\n\n" +
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    priority="high"
                )
        
    except Exception as e:
        logger.error(f"Error checking system anomalies: {e}")
        results["error"] = str(e)
    
    return results


def check_api_anomalies(config, notifier=None) -> Dict[str, Any]:
    """
    Check for anomalies in API metrics.
    
    Args:
        config: Application configuration
        notifier: Optional notification service
        
    Returns:
        Dictionary with anomaly detection results
    """
    logger.info("Checking for API anomalies")
    
    detector = AnomalyDetector(config)
    results = {
        "anomalies": [],
        "outliers": [],
        "trends": []
    }
    
    try:
        # Load API metrics from disk if available
        api_metrics_file = "data/exchange_api_summary.json"
        if not os.path.exists(api_metrics_file):
            return {
                "status": "no_data",
                "message": "No API metrics data available"
            }
        
        with open(api_metrics_file, "r") as f:
            api_data = json.load(f)
        
        # Process each exchange
        for exchange_name, exchange_data in api_data.get("exchanges", {}).items():
            if "avg_response_time" in exchange_data:
                # Add response time to metrics history
                detector.add_metric(
                    f"{exchange_name}_response_time",
                    exchange_data["avg_response_time"],
                    "api"
                )
                
                # Check for anomalies in response time
                anomaly_result = detector.detect_anomalies_zscore(
                    "api", f"{exchange_name}_response_time"
                )
                
                outlier_result = detector.detect_outliers_iqr(
                    "api", f"{exchange_name}_response_time"
                )
                
                trend_result = detector.detect_trend(
                    "api", f"{exchange_name}_response_time"
                )
                
                # Collect results
                if "is_anomaly" in anomaly_result and anomaly_result["is_anomaly"]:
                    results["anomalies"].append(anomaly_result)
                
                if "is_outlier" in outlier_result and outlier_result["is_outlier"]:
                    results["outliers"].append(outlier_result)
                
                if "trend" in trend_result and trend_result["trend"] != "stable":
                    results["trends"].append(trend_result)
        
        # Send notifications if anomalies detected and notifier available
        if notifier and (results["anomalies"] or results["outliers"]):
            anomaly_messages = []
            
            for anomaly in results["anomalies"]:
                metric = anomaly["metric"]
                value = anomaly["latest_value"]
                message = f"{metric}: {value:.2f}ms (Z-score: {anomaly['z_score']:.2f})"
                anomaly_messages.append(message)
            
            for outlier in results["outliers"]:
                metric = outlier["metric"]
                value = outlier["latest_value"]
                message = f"{metric}: {value:.2f}ms (Outside IQR bounds: {outlier['lower_bound']:.2f}-{outlier['upper_bound']:.2f}ms)"
                anomaly_messages.append(message)
            
            if anomaly_messages:
                notifier.send_alert(
                    "⚠️ API ANOMALY DETECTION ALERT\n\n" +
                    "The following API metrics show anomalous behavior:\n\n" +
                    "- " + "\n- ".join(anomaly_messages) + "\n\n" +
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    priority="high"
                )
                
    except Exception as e:
        logger.error(f"Error checking API anomalies: {e}")
        results["error"] = str(e)
    
    return results
