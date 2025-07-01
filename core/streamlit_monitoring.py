"""Tiny helpers for Streamlit monitoring decorators used in tests."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from .monitoring import structured_logger


def streamlit_monitor(func: Callable) -> Callable:
    """Decorator that logs entry and exit of a Streamlit function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        structured_logger.info("streamlit monitor start", extra={"function": func.__name__})
        result = func(*args, **kwargs)
        structured_logger.info("streamlit monitor end", extra={"function": func.__name__})
        return result

    return wrapper


def streamlit_page(name: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            structured_logger.info("streamlit page", extra={"page": name})
            return func(*args, **kwargs)

        return wrapper

    return decorator


def streamlit_component(name: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            structured_logger.info("streamlit component", extra={"component": name})
            return func(*args, **kwargs)

        return wrapper

    return decorator

