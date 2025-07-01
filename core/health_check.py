from __future__ import annotations

"""Minimal health check utilities for WhisperForge."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict

@dataclass
class HealthStatus:
    status: str
    timestamp: str

    # Optional fields for backward compatibility
    uptime_seconds: float = 0.0


@dataclass
class SloMetrics:
    error_rate_5xx: float = 0.0
    median_response_time: int = 0
    active_users_1h: int = 0


class HealthChecker:
    """Simple health check implementation."""

    def get_health_status(self) -> HealthStatus:
        return HealthStatus(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=0.0,
        )

    def get_slo_metrics(self) -> SloMetrics:
        """Return placeholder SLO metrics."""
        return SloMetrics()

    def check_slo_violations(self) -> list:
        return []

    def get_metrics_json(self) -> str:
        data: Dict[str, Any] = {
            "health": asdict(self.get_health_status()),
            "slo_metrics": asdict(self.get_slo_metrics()),
        }
        import json

        return json.dumps(data)


health_checker = HealthChecker()
