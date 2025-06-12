"""
Prometheus Metrics Exporter
===========================

Exports WhisperForge metrics in Prometheus format for external monitoring
systems like Grafana, AlertManager, etc.
"""

import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
from datetime import datetime, timedelta

from .monitoring import structured_logger
from .health_check import health_checker


@dataclass
class MetricValue:
    """Prometheus metric value with labels"""
    value: float
    labels: Dict[str, str]
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class PrometheusExporter:
    """Exports metrics in Prometheus format"""
    
    def __init__(self):
        self.logger = structured_logger
        self.metrics = defaultdict(list)
        self.counters = defaultdict(float)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.lock = threading.Lock()
        
        # Initialize base metrics
        self._init_base_metrics()
    
    def _init_base_metrics(self):
        """Initialize base metrics"""
        self.register_gauge("whisperforge_health_status", "Overall health status (0=unhealthy, 1=degraded, 2=healthy)")
        self.register_counter("whisperforge_http_requests_total", "Total HTTP requests")
        self.register_histogram("whisperforge_request_duration_seconds", "Request duration in seconds")
        self.register_counter("whisperforge_pipeline_success_total", "Total successful pipeline executions")
        self.register_counter("whisperforge_pipeline_failure_total", "Total failed pipeline executions")
        self.register_histogram("whisperforge_pipeline_duration_seconds", "Pipeline duration in seconds")
        self.register_gauge("whisperforge_active_users_1h", "Active users in the last hour")
        self.register_gauge("whisperforge_database_response_time_ms", "Database response time in milliseconds")
        self.register_gauge("whisperforge_cpu_usage_percent", "CPU usage percentage")
        self.register_gauge("whisperforge_memory_usage_percent", "Memory usage percentage")
        self.register_gauge("whisperforge_slo_compliance_percentage", "SLO compliance percentage")
    
    def register_counter(self, name: str, help_text: str):
        """Register a counter metric"""
        self.counters[name] = 0.0
    
    def register_gauge(self, name: str, help_text: str):
        """Register a gauge metric"""
        self.gauges[name] = 0.0
    
    def register_histogram(self, name: str, help_text: str):
        """Register a histogram metric"""
        self.histograms[name] = []
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            key = self._make_key(name, labels or {})
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value"""
        with self.lock:
            key = self._make_key(name, labels or {})
            self.gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Add an observation to a histogram"""
        with self.lock:
            key = self._make_key(name, labels or {})
            self.histograms[key].append(value)
            
            # Keep only recent observations (last 1000)
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
    
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create a unique key for metric with labels"""
        if not labels:
            return name
        
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def _parse_key(self, key: str) -> tuple:
        """Parse metric key into name and labels"""
        if '{' not in key:
            return key, {}
        
        name, label_part = key.split('{', 1)
        label_part = label_part.rstrip('}')
        
        labels = {}
        if label_part:
            for pair in label_part.split(','):
                k, v = pair.split('=', 1)
                labels[k] = v.strip('"')
        
        return name, labels
    
    def update_health_metrics(self):
        """Update health-related metrics"""
        try:
            health_status = health_checker.get_health_status()
            
            # Convert health status to numeric
            status_map = {"healthy": 2, "degraded": 1, "unhealthy": 0}
            self.set_gauge("whisperforge_health_status", status_map.get(health_status.status, 0))
            
            # Database metrics
            db_check = health_status.checks.get("database", {})
            if "response_time_ms" in db_check:
                self.set_gauge("whisperforge_database_response_time_ms", db_check["response_time_ms"])
            
            # Performance metrics
            perf_check = health_status.checks.get("performance", {})
            if "cpu_percent" in perf_check and perf_check["cpu_percent"] is not None:
                self.set_gauge("whisperforge_cpu_usage_percent", perf_check["cpu_percent"])
            if "memory_percent" in perf_check and perf_check["memory_percent"] is not None:
                self.set_gauge("whisperforge_memory_usage_percent", perf_check["memory_percent"])
            
        except Exception as e:
            self.logger.error("Failed to update health metrics", error=e)
    
    def update_slo_metrics(self):
        """Update SLO-related metrics"""
        try:
            slo_metrics = health_checker.get_slo_metrics()
            
            # Active users
            self.set_gauge("whisperforge_active_users_1h", slo_metrics.active_users_1h)
            
            # Calculate SLO compliance
            violations = health_checker.check_slo_violations()
            compliance = 100.0 if not violations else max(0, 100 - len(violations) * 10)
            self.set_gauge("whisperforge_slo_compliance_percentage", compliance)
            
        except Exception as e:
            self.logger.error("Failed to update SLO metrics", error=e)
    
    def track_request(self, duration_seconds: float, status_code: int, method: str = "GET", endpoint: str = "/"):
        """Track HTTP request metrics"""
        labels = {
            "method": method,
            "endpoint": endpoint,
            "status": str(status_code)
        }
        
        self.increment_counter("whisperforge_http_requests_total", labels=labels)
        self.observe_histogram("whisperforge_request_duration_seconds", duration_seconds, labels=labels)
    
    def track_pipeline(self, pipeline_type: str, duration_seconds: float, success: bool):
        """Track pipeline execution metrics"""
        labels = {"pipeline_type": pipeline_type}
        
        if success:
            self.increment_counter("whisperforge_pipeline_success_total", labels=labels)
        else:
            self.increment_counter("whisperforge_pipeline_failure_total", labels=labels)
        
        self.observe_histogram("whisperforge_pipeline_duration_seconds", duration_seconds, labels=labels)
    
    def export_metrics(self) -> str:
        """Export all metrics in Prometheus format"""
        lines = []
        
        # Update dynamic metrics
        self.update_health_metrics()
        self.update_slo_metrics()
        
        with self.lock:
            # Export counters
            for key, value in self.counters.items():
                name, labels = self._parse_key(key)
                if labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                    lines.append(f'{name}{{{label_str}}} {value}')
                else:
                    lines.append(f'{name} {value}')
            
            # Export gauges
            for key, value in self.gauges.items():
                name, labels = self._parse_key(key)
                if labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                    lines.append(f'{name}{{{label_str}}} {value}')
                else:
                    lines.append(f'{name} {value}')
            
            # Export histograms (simplified - just count and sum)
            for key, values in self.histograms.items():
                if not values:
                    continue
                
                name, labels = self._parse_key(key)
                label_str = ""
                if labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                    label_str = "{" + label_str + "}"
                
                count = len(values)
                total = sum(values)
                
                lines.append(f'{name}_count{label_str} {count}')
                lines.append(f'{name}_sum{label_str} {total}')
                
                # Add quantiles
                if values:
                    sorted_values = sorted(values)
                    quantiles = [0.5, 0.95, 0.99]
                    for q in quantiles:
                        idx = int(q * len(sorted_values))
                        idx = min(idx, len(sorted_values) - 1)
                        value = sorted_values[idx]
                        
                        q_label = f'quantile="{q}"'
                        if labels:
                            full_label = "{" + ",".join([q_label] + [f'{k}="{v}"' for k, v in labels.items()]) + "}"
                        else:
                            full_label = "{" + q_label + "}"
                        
                        lines.append(f'{name}{full_label} {value}')
        
        return "\n".join(lines) + "\n"
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """Get metrics as dictionary for JSON export"""
        with self.lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {k: {"count": len(v), "sum": sum(v)} for k, v in self.histograms.items()},
                "timestamp": time.time()
            }


# Global metrics exporter
metrics_exporter = PrometheusExporter()


# Convenience functions
def track_request(duration_seconds: float, status_code: int, method: str = "GET", endpoint: str = "/"):
    """Track HTTP request"""
    metrics_exporter.track_request(duration_seconds, status_code, method, endpoint)


def track_pipeline(pipeline_type: str, duration_seconds: float, success: bool):
    """Track pipeline execution"""
    metrics_exporter.track_pipeline(pipeline_type, duration_seconds, success)


def increment_counter(name: str, value: float = 1.0, **labels):
    """Increment counter metric"""
    metrics_exporter.increment_counter(name, value, labels)


def set_gauge(name: str, value: float, **labels):
    """Set gauge metric"""
    metrics_exporter.set_gauge(name, value, labels)


def observe_histogram(name: str, value: float, **labels):
    """Add histogram observation"""
    metrics_exporter.observe_histogram(name, value, labels)


def export_prometheus_metrics() -> str:
    """Export metrics in Prometheus format"""
    return metrics_exporter.export_metrics()


def export_json_metrics() -> Dict[str, Any]:
    """Export metrics as JSON"""
    return metrics_exporter.get_metrics_dict() 