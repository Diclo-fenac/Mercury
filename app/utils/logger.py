"""
Structured Logging Utility
"""
import logging
import sys
from typing import Any, Dict, Optional


def setup_logging(log_level: str = "INFO"):
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


class StructuredLogger:
    """Structured logger with context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def log_request(self, method: str, path: str, user_id: Optional[str] = None, **kwargs):
        """Log API request"""
        context = {
            "event": "api_request",
            "method": method,
            "path": path,
            "user_id": user_id,
            **kwargs
        }
        self.logger.info(f"API Request: {method} {path}", extra=context)
    
    def log_service_call(self, service: str, method: str, **kwargs):
        """Log service call"""
        context = {
            "event": "service_call",
            "service": service,
            "method": method,
            **kwargs
        }
        self.logger.info(f"Service Call: {service}.{method}", extra=context)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log error with context"""
        self.logger.error(
            f"Error: {str(error)}",
            exc_info=True,
            extra={"event": "error", "context": context or {}}
        )
    
    def log_websocket_event(self, event: str, user_id: Optional[str] = None, **kwargs):
        """Log WebSocket event"""
        context = {
            "event": "websocket",
            "ws_event": event,
            "user_id": user_id,
            **kwargs
        }
        self.logger.info(f"WebSocket: {event}", extra=context)
