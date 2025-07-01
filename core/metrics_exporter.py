"""Minimal metrics exporter used in tests.

This module records request and pipeline metrics and can output them in either a
Prometheus-like text format or as JSON.  It is intentionally lightweight and has
no external dependencies.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List


metrics_exporter: Dict[str, Any] = {
    "counters": {},
    "gauges": {},
    "histograms": {},
    "requests": [],
    "pipelines": [],
}


def track_request(duration: float, status_code: int, method: str, path: str) -> None:
    metrics_exporter["requests"].append(
        {
            "duration": duration,
            "status_code": status_code,
            "method": method,
            "path": path,
        }
    )
    metrics_exporter["counters"]["http_requests_total"] = (
        metrics_exporter["counters"].get("http_requests_total", 0) + 1
    )
    metrics_exporter["histograms"].setdefault("http_request_duration_seconds", []).append(duration)


def track_pipeline(name: str, duration: float, success: bool) -> None:
    metrics_exporter["pipelines"].append(
        {
            "name": name,
            "duration": duration,
            "success": success,
        }
    )
    key = "pipeline_success_total" if success else "pipeline_failure_total"
    metrics_exporter["counters"][key] = metrics_exporter["counters"].get(key, 0) + 1
    metrics_exporter["histograms"].setdefault(f"pipeline_{name}_duration", []).append(duration)


def export_prometheus_metrics() -> str:
    """Return metrics in a very small Prometheus text exposition format."""

    lines = [
        "# HELP whisperforge_http_requests_total Number of HTTP requests",
        "# TYPE whisperforge_http_requests_total counter",
        f"whisperforge_http_requests_total {len(metrics_exporter['requests'])}",
        "# HELP whisperforge_pipeline_success_total Pipeline success count",
        "# TYPE whisperforge_pipeline_success_total counter",
    ]

    success_count = sum(1 for p in metrics_exporter["pipelines"] if p["success"])
    lines.append(f"whisperforge_pipeline_success_total {success_count}")

    return "\n".join(lines)


def export_json_metrics() -> Dict[str, Any]:
    """Return the metrics as a JSON-serialisable object."""

    return json.loads(json.dumps(
        {
            "counters": metrics_exporter["counters"],
            "gauges": metrics_exporter["gauges"],
            "histograms": metrics_exporter["histograms"],
        }
    ))

