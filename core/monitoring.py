"""Simplified monitoring utilities used for testing.

This module provides lightweight stand-ins for the original monitoring system so
that the test suite in ``scripts/test_monitoring.py`` can run without requiring
external services.  Only the small subset of features exercised by the tests are
implemented here.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------

class StructuredLogger(logging.LoggerAdapter):
    """Minimal structured logger used in tests."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        extra = kwargs.pop("extra", {})
        # treat any additional keyword arguments as structured fields
        extra.update({k: kwargs.pop(k) for k in list(kwargs)})
        if extra:
            context = " ".join(f"{k}={v}" for k, v in extra.items())
            msg = f"{msg} [{context}]"
        kwargs["extra"] = extra
        return msg, kwargs

    def pipeline_start(self, name: str, user_id: Optional[str] = None) -> None:
        self.info("pipeline start", extra={"pipeline": name, "user_id": user_id})

    def pipeline_complete(self, name: str, duration: float, success: bool = True) -> None:
        self.info(
            "pipeline complete",
            extra={"pipeline": name, "duration": duration, "success": success},
        )


structured_logger = StructuredLogger(logger, {})


def set_trace_context(user_id: Optional[str] = None, operation: Optional[str] = None) -> str:
    """Create a trace context and log it."""

    trace_id = str(uuid.uuid4())
    structured_logger.info(
        "trace context created",
        extra={"trace_id": trace_id, "user_id": user_id, "operation": operation},
    )
    return trace_id


@contextmanager
def trace_operation(operation: str, user_id: Optional[str] = None):
    """Context manager that logs a trace when the block executes."""

    trace_id = set_trace_context(user_id=user_id, operation=operation)
    try:
        yield trace_id
    finally:
        structured_logger.info(
            "trace operation finished",
            extra={"trace_id": trace_id, "operation": operation},
        )


# ---------------------------------------------------------------------------
# Error tracking
# ---------------------------------------------------------------------------

class ErrorTracker:
    def capture_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        structured_logger.error(
            f"captured exception: {exc}", extra={"context": context}
        )

    def capture_message(self, message: str, level: str = "info", context: Optional[Dict[str, Any]] = None) -> None:
        getattr(structured_logger, level)(message, extra={"context": context})


error_tracker = ErrorTracker()


# ---------------------------------------------------------------------------
# Performance tracking
# ---------------------------------------------------------------------------

class PerformanceTracker:
    @contextmanager
    def track_operation(self, name: str):
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            structured_logger.info(
                "operation timing",
                extra={"operation": name, "duration": duration},
            )

    def track_pipeline_performance(
        self, name: str, duration: float, success: bool, file_size_mb: Optional[int] = None
    ) -> None:
        structured_logger.info(
            "pipeline metrics",
            extra={
                "pipeline": name,
                "duration": duration,
                "success": success,
                "file_size_mb": file_size_mb,
            },
        )


performance_tracker = PerformanceTracker()


def monitor_function(name: str):
    """Decorator that times the wrapped function using ``PerformanceTracker``."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with performance_tracker.track_operation(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Compatibility helpers used by other modules
# ---------------------------------------------------------------------------

def init_monitoring() -> bool:
    structured_logger.info("Monitoring initialised")
    return True


def track_error(error: Exception, context: str = "") -> None:
    error_tracker.capture_exception(error, {"context": context})


def track_performance(operation: str, duration: float) -> None:
    performance_tracker.track_pipeline_performance(operation, duration, True)


def track_user_action(action: str, user_id: Optional[str] = None) -> None:
    structured_logger.info("user action", extra={"action": action, "user_id": user_id})


def track_page(page: str, user_id: Optional[str] = None) -> None:
    structured_logger.info("page view", extra={"page": page, "user_id": user_id})


def get_health_status() -> Dict[str, Any]:
    return {"status": "healthy", "monitoring": "basic", "timestamp": "now"}


class MonitoringManager:
    """Backwards compatibility wrapper used in a few places."""

    def __init__(self) -> None:
        self.enabled = False

    def track_error(self, error: Exception, context: str = "") -> None:
        track_error(error, context)

    def track_performance(self, operation: str, duration: float) -> None:
        track_performance(operation, duration)

    def track_user_action(self, action: str, user_id: Optional[str] = None) -> None:
        track_user_action(action, user_id)


def get_monitoring_manager() -> MonitoringManager:
    return MonitoringManager()

