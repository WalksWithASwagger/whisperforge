"""
Streamlit Monitoring Integration
===============================

Integrates the core monitoring system with Streamlit applications,
providing request tracking, user session monitoring, and performance metrics.
"""

import time
import streamlit as st
from typing import Dict, Any, Optional
from functools import wraps
from contextlib import contextmanager

from .monitoring import (
    structured_logger, 
    performance_tracker, 
    error_tracker,
    set_trace_context,
    trace_operation,
    monitor_function
)


class StreamlitMonitor:
    """Streamlit-specific monitoring wrapper"""
    
    def __init__(self):
        self.logger = structured_logger
        self.performance = performance_tracker
        self.errors = error_tracker
    
    def init_session_monitoring(self):
        """Initialize monitoring for Streamlit session"""
        # Generate trace ID for this session if not exists
        if 'trace_id' not in st.session_state:
            import uuid
            st.session_state.trace_id = str(uuid.uuid4())
        
        # Set trace context
        user_id = getattr(st.session_state, 'user_id', None)
        session_id = getattr(st.session_state, 'session_id', None)
        
        set_trace_context(
            trace_id=st.session_state.trace_id,
            user_id=user_id,
            session_id=session_id,
            operation='streamlit_session'
        )
        
        # Log session start if new
        if 'session_monitored' not in st.session_state:
            self.logger.info(
                "Streamlit session started",
                event_type='session_start',
                user_authenticated=bool(user_id),
                page=self._get_current_page()
            )
            st.session_state.session_monitored = True
    
    def _get_current_page(self) -> str:
        """Get current page name from Streamlit"""
        try:
            # Try to get from query params or session state
            query_params = st.experimental_get_query_params()
            if 'page' in query_params:
                return query_params['page'][0]
            return getattr(st.session_state, 'current_page', 'home')
        except:
            return 'unknown'
    
    def track_page_view(self, page_name: str):
        """Track page view"""
        st.session_state.current_page = page_name
        
        self.logger.user_action(
            'page_view',
            user_id=getattr(st.session_state, 'user_id', None),
            page=page_name,
            authenticated=bool(getattr(st.session_state, 'user_id', None))
        )
    
    def track_user_action(self, action: str, **context):
        """Track user action with Streamlit context"""
        user_id = getattr(st.session_state, 'user_id', None)
        
        action_context = {
            'page': self._get_current_page(),
            'authenticated': bool(user_id),
            **context
        }
        
        self.logger.user_action(action, user_id=user_id, **action_context)
    
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track error with Streamlit context"""
        error_context = {
            'page': self._get_current_page(),
            'user_id': getattr(st.session_state, 'user_id', None),
            'session_id': getattr(st.session_state, 'session_id', None),
            **(context or {})
        }
        
        self.errors.capture_exception(error, error_context)
    
    @contextmanager
    def track_operation(self, operation_name: str, **context):
        """Track operation performance in Streamlit context"""
        operation_context = {
            'page': self._get_current_page(),
            'user_id': getattr(st.session_state, 'user_id', None),
            **context
        }
        
        with self.performance.track_operation(operation_name, **operation_context):
            yield
    
    def monitor_pipeline(self, pipeline_type: str):
        """Decorator for monitoring pipeline operations"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                user_id = getattr(st.session_state, 'user_id', None)
                
                # Log pipeline start
                self.logger.pipeline_start(pipeline_type, user_id=user_id)
                
                start_time = time.time()
                try:
                    with self.track_operation(f'pipeline_{pipeline_type}'):
                        result = func(*args, **kwargs)
                    
                    duration = time.time() - start_time
                    self.logger.pipeline_complete(pipeline_type, duration, success=True)
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    self.logger.pipeline_complete(pipeline_type, duration, success=False)
                    self.track_error(e, {'pipeline_type': pipeline_type})
                    raise
            
            return wrapper
        return decorator
    
    def show_performance_metrics(self):
        """Display performance metrics in Streamlit sidebar (dev mode)"""
        if st.sidebar.checkbox("Show Performance Metrics", value=False):
            with st.sidebar.expander("Performance Metrics"):
                # Show current trace ID
                if hasattr(st.session_state, 'trace_id'):
                    st.code(f"Trace ID: {st.session_state.trace_id}")
                
                # Show session info
                user_id = getattr(st.session_state, 'user_id', 'Anonymous')
                st.write(f"User: {user_id}")
                st.write(f"Page: {self._get_current_page()}")
                
                # Show recent performance data (if available)
                st.write("Monitoring active ✅")


# Global Streamlit monitor instance
streamlit_monitor = StreamlitMonitor()


# Convenience functions for easy integration
def init_monitoring():
    """Initialize Streamlit monitoring - call at app start"""
    streamlit_monitor.init_session_monitoring()


def track_page(page_name: str):
    """Track page view"""
    streamlit_monitor.track_page_view(page_name)


def track_action(action: str, **context):
    """Track user action"""
    streamlit_monitor.track_user_action(action, **context)


def track_error(error: Exception, context: Dict[str, Any] = None):
    """Track error"""
    streamlit_monitor.track_error(error, context)


@contextmanager
def track_operation(operation_name: str, **context):
    """Track operation performance"""
    with streamlit_monitor.track_operation(operation_name, **context):
        yield


def monitor_pipeline(pipeline_type: str):
    """Monitor pipeline decorator"""
    return streamlit_monitor.monitor_pipeline(pipeline_type)


def show_dev_metrics():
    """Show development metrics in sidebar"""
    streamlit_monitor.show_performance_metrics()


# Streamlit-specific decorators
def streamlit_page(page_name: str):
    """Decorator for Streamlit page functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Initialize monitoring
            init_monitoring()
            
            # Track page view
            track_page(page_name)
            
            # Execute page function with monitoring
            try:
                with track_operation(f'page_{page_name}'):
                    return func(*args, **kwargs)
            except Exception as e:
                track_error(e, {'page': page_name})
                raise
        
        return wrapper
    return decorator


def streamlit_component(component_name: str):
    """Decorator for Streamlit component functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                with track_operation(f'component_{component_name}'):
                    return func(*args, **kwargs)
            except Exception as e:
                track_error(e, {'component': component_name})
                raise
        
        return wrapper
    return decorator 