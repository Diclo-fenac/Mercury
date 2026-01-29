"""
API Logger Adapter
Simple logger adapter for API endpoints
"""
from app.utils.logger import get_logger


class APILogger:
    """Simple logger adapter for API endpoints"""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def log_request(self, method: str, path: str, user_id: str = None, **kwargs):
        """Log API request"""
        self.logger.info(f"{method} {path}", extra={"user_id": user_id, **kwargs})
    
    def log_service_call(self, service: str, method: str, user_id: str = None, **kwargs):
        """Log service call"""
        self.logger.info(f"Service call: {service}.{method}", extra={"user_id": user_id, **kwargs})
    
    def log_error(self, error: Exception, context: dict = None):
        """Log error"""
        self.logger.error(f"Error: {error}", extra=context or {})
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)