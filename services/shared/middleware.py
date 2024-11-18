import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            response.headers['X-Request-ID'] = request_id
            return response
        except Exception as e:
            # Log the error with request_id
            logger.error(f"Request failed", 
                        extra={"request_id": request_id, 
                               "path": request.url.path,
                               "method": request.method})
            raise 