"""
Logging Configuration
Structured logging setup for FastAPI application
"""
import logging
import sys
from typing import Dict, Any
from datetime import datetime

from app.core.config import get_settings

class ColoredFormatter(logging.Formatter):
    """Colored log formatter for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logging():
    """Setup application logging"""
    settings = get_settings()
    
    # Create formatter
    formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    
    # App-specific loggers
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(f"app.{name}")

class StructuredLogger:
    """Structured logger for better observability"""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def log_request(self, method: str, path: str, user_id: str = None, **kwargs):
        """Log HTTP request"""
        self.logger.info(
            f"🌐 {method} {path}",
            extra={
                "event_type": "http_request",
                "method": method,
                "path": path,
                "user_id": user_id,
                **kwargs
            }
        )
    
    def log_service_call(self, service: str, method: str, duration: float = None, **kwargs):
        """Log service method call"""
        duration_str = f" ({duration:.2f}s)" if duration else ""
        self.logger.info(
            f"🔧 {service}.{method}{duration_str}",
            extra={
                "event_type": "service_call",
                "service": service,
                "method": method,
                "duration": duration,
                **kwargs
            }
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        self.logger.error(
            f"💥 {type(error).__name__}: {str(error)}",
            extra={
                "event_type": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {}
            },
            exc_info=True
        )
    
    def log_websocket_event(self, event: str, user_id: str = None, **kwargs):
        """Log WebSocket event"""
        self.logger.info(
            f"🔌 WebSocket: {event}",
            extra={
                "event_type": "websocket",
                "event": event,
                "user_id": user_id,
                **kwargs
            }
        )