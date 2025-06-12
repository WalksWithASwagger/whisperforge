"""
Monitoring and Analytics Module for WhisperForge
================================================

Handles error tracking, performance monitoring, and user analytics.
"""

import os
import time
import logging
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Global performance tracking
_request_start_time = None
_performance_metrics = []

def init_monitoring():
    """Initialize monitoring services"""
    try:
        # Initialize Sentry for error tracking
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            import sentry_sdk
            from sentry_sdk.integrations.streamlit import StreamlitIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    StreamlitIntegration(),
                    LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
                ],
                traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
                environment=os.getenv("ENVIRONMENT", "production"),
                release=os.getenv("APP_VERSION", "1.0.0")
            )
            logger.info("Sentry monitoring initialized successfully")
        else:
            logger.warning("SENTRY_DSN not set - error tracking disabled")
            
    except ImportError:
        logger.error("Sentry SDK not installed - monitoring disabled")
    except Exception as e:
        logger.error(f"Failed to initialize monitoring: {e}")

def track_error(error: Exception, context: Dict[str, Any] = None):
    """Track an error with context"""
    try:
        import sentry_sdk
        
        if context:
            sentry_sdk.set_context("error_context", context)
            
        # Add user context if available
        if hasattr(st.session_state, 'user_id') and st.session_state.user_id:
            sentry_sdk.set_user({
                "id": st.session_state.user_id,
                "authenticated": st.session_state.get("authenticated", False)
            })
            
        sentry_sdk.capture_exception(error)
        logger.error(f"Error tracked: {error}", exc_info=True)
        
    except Exception as e:
        # Fallback to basic logging if Sentry fails
        logger.error(f"Failed to track error to Sentry: {e}")
        logger.error(f"Original error: {error}", exc_info=True)

@contextmanager
def track_performance(operation_name: str, context: Dict[str, Any] = None):
    """Context manager to track operation performance"""
    start_time = time.time()
    
    try:
        import sentry_sdk
        with sentry_sdk.start_transaction(op="function", name=operation_name):
            yield
    except ImportError:
        yield
    finally:
        duration = time.time() - start_time
        
        # Log performance metrics
        logger.info(f"Performance: {operation_name} took {duration:.2f}s", extra={
            "operation": operation_name,
            "duration": duration,
            "context": context or {}
        })
        
        # Store metrics for analytics
        _performance_metrics.append({
            "operation": operation_name,
            "duration": duration,
            "timestamp": datetime.now(),
            "context": context or {}
        })

def track_user_action(action: str, details: Dict[str, Any] = None):
    """Track user actions for analytics"""
    try:
        # Get user info from session
        user_id = getattr(st.session_state, 'user_id', None)
        
        event_data = {
            "action": action,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "session_id": st.session_state.get("session_id", "unknown")
        }
        
        # Log for analytics
        logger.info(f"User action: {action}", extra=event_data)
        
        # Send to Sentry as breadcrumb
        try:
            import sentry_sdk
            sentry_sdk.add_breadcrumb(
                message=f"User action: {action}",
                category="user_action",
                data=event_data,
                level="info"
            )
        except ImportError:
            pass
            
    except Exception as e:
        logger.error(f"Failed to track user action: {e}")

def get_health_status() -> Dict[str, Any]:
    """Get application health status"""
    try:
        from core.supabase_integration import get_supabase_client
        
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Check database connection
        try:
            db = get_supabase_client()
            if db and db.test_connection():
                health["checks"]["database"] = "healthy"
            else:
                health["checks"]["database"] = "unhealthy"
                health["status"] = "degraded"
        except Exception as e:
            health["checks"]["database"] = f"error: {str(e)}"
            health["status"] = "unhealthy"
        
        # Check AI providers
        ai_providers = {}
        if os.getenv("OPENAI_API_KEY"):
            ai_providers["openai"] = "configured"
        if os.getenv("ANTHROPIC_API_KEY"):
            ai_providers["anthropic"] = "configured"
        if os.getenv("GROK_API_KEY"):
            ai_providers["grok"] = "configured"
            
        health["checks"]["ai_providers"] = ai_providers
        
        # Check environment variables
        required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "JWT_SECRET"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            health["checks"]["environment"] = f"missing: {', '.join(missing_vars)}"
            health["status"] = "unhealthy"
        else:
            health["checks"]["environment"] = "healthy"
        
        return health
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def get_performance_metrics(hours: int = 24) -> Dict[str, Any]:
    """Get performance metrics for the last N hours"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent metrics
        recent_metrics = [
            m for m in _performance_metrics 
            if m["timestamp"] > cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": "No recent metrics available"}
        
        # Calculate statistics
        durations = [m["duration"] for m in recent_metrics]
        operations = {}
        
        for metric in recent_metrics:
            op = metric["operation"]
            if op not in operations:
                operations[op] = []
            operations[op].append(metric["duration"])
        
        # Aggregate by operation
        operation_stats = {}
        for op, times in operations.items():
            operation_stats[op] = {
                "count": len(times),
                "avg_duration": sum(times) / len(times),
                "max_duration": max(times),
                "min_duration": min(times)
            }
        
        return {
            "period_hours": hours,
            "total_operations": len(recent_metrics),
            "avg_duration": sum(durations) / len(durations),
            "operations": operation_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return {"error": str(e)}

def init_session_tracking():
    """Initialize session tracking for analytics"""
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
        
    if "session_start" not in st.session_state:
        st.session_state.session_start = datetime.now()
        
    # Track page views
    track_user_action("page_view", {
        "page": st.session_state.get("current_page", "Home"),
        "authenticated": st.session_state.get("authenticated", False)
    })

# ---------------------------------------------------------------------------
# Lightweight wrappers for backward-compatibility with monitoring tests
# ---------------------------------------------------------------------------

from contextlib import contextmanager as _ctx_mngr
from typing import Callable as _Callable, Any as _Any

class _StructuredLoggerAdapter(logging.LoggerAdapter):
    """Passthrough adapter that attaches arbitrary kwargs as extra."""

    def process(self, msg, kwargs):
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)  # treat arbitrary kwargs as extra
        return msg, {"extra": extra}

    # Convenience wrappers used in tests
    def pipeline_start(self, pipeline: str, **kwargs):
        self.info("🔄 Pipeline start", pipeline=pipeline, **kwargs)

    def pipeline_complete(self, pipeline: str, duration: float, success: bool = True, **kwargs):
        level = logging.INFO if success else logging.WARNING
        self.log(level, "✅ Pipeline complete", pipeline=pipeline, duration=duration, success=success, **kwargs)

# Expose a structured_logger that accepts **kwargs in log calls
structured_logger = _StructuredLoggerAdapter(logger, {})  # type: ignore

# Simple trace context using a thread-local store
_trace_context: Dict[str, Any] = {}

def set_trace_context(**kwargs):
    """Set global trace context (very lightweight)."""
    _trace_context.update(kwargs)
    return _trace_context.get("trace_id", "no-trace")

@_ctx_mngr
def trace_operation(name: str, **kwargs):
    """Context manager that logs the start/end of an operation."""
    structured_logger.info("🔄 trace_operation start", operation=name, **kwargs)
    start = time.time()
    try:
        yield
    finally:
        structured_logger.info(
            "✅ trace_operation end",
            operation=name,
            duration=time.time() - start,
            **kwargs,
        )

class _ErrorTracker:
    def capture_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None):
        structured_logger.error(f"Captured exception: {exc}", context=context)

    def capture_message(self, message: str, level: str = "info", context: Optional[Dict[str, Any]] = None):
        getattr(structured_logger, level, structured_logger.info)(message, context=context)

error_tracker = _ErrorTracker()

class _PerformanceTracker:
    @_ctx_mngr
    def track_operation(self, name: str):
        with trace_operation(name):
            yield

    def track_pipeline_performance(self, pipeline: str, duration: float, success: bool, **kwargs):
        structured_logger.info(
            "Pipeline performance",
            pipeline=pipeline,
            duration=duration,
            success=success,
            **kwargs,
        )

performance_tracker = _PerformanceTracker()

def monitor_function(name: str):
    def decorator(fn: _Callable[..., _Any]):
        def wrapper(*args, **kwargs):
            with trace_operation(name):
                return fn(*args, **kwargs)
        return wrapper
    return decorator 