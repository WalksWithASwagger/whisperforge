from prometheus_client import Counter, Histogram
from fastapi import FastAPI


def setup_metrics(app: FastAPI, service_name: str):
    # Request counters
    request_count = Counter(
        f"{service_name}_requests_total", f"Total {service_name} requests"
    )

    # Response time histogram
    request_time = Histogram(
        f"{service_name}_request_duration_seconds",
        f"{service_name} request duration in seconds",
    )

    @app.middleware("http")
    async def track_metrics(request, call_next):
        request_count.inc()
        with request_time.time():
            response = await call_next(request)
        return response
