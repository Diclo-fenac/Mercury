"""
Structured Logging Utility
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(datetime.UTC).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "trace_id") and record.trace_id:
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "tenant_id") and record.tenant_id:
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, "event") and record.event:
            log_data["event"] = record.event
        if hasattr(record, "context") and record.context:
            log_data["context"] = record.context
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO"):
    """Setup application logging"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to prevent duplicates
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


class StructuredLogger:
    """Structured logger with context"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def log_request(self, method: str, path: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None, trace_id: Optional[str] = None, **kwargs):
        """Log API request"""
        extra = {
            "event": "api_request",
            "user_id": user_id,
            "tenant_id": tenant_id,
            "trace_id": trace_id,
            "context": kwargs
        }
        self.logger.info(f"API Request: {method} {path}", extra=extra)
    
    def log_service_call(self, service: str, method: str, tenant_id: Optional[str] = None, trace_id: Optional[str] = None, **kwargs):
        """Log service call"""
        extra = {
            "event": "service_call",
            "service": service,
            "method": method,
            "tenant_id": tenant_id,
            "trace_id": trace_id,
            "context": kwargs
        }
        self.logger.info(f"Service Call: {service}.{method}", extra=extra)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None, tenant_id: Optional[str] = None, trace_id: Optional[str] = None):
        """Log error with context"""
        extra = {
            "event": "error", 
            "context": context or {},
            "tenant_id": tenant_id,
            "trace_id": trace_id
        }
        self.logger.error(
            f"Error: {str(error)}",
            exc_info=True,
            extra=extra
        )
    
    def log_websocket_event(self, event: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None, trace_id: Optional[str] = None, **kwargs):
        """Log WebSocket event"""
        extra = {
            "event": "websocket",
            "ws_event": event,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "trace_id": trace_id,
            "context": kwargs
        }
        self.logger.info(f"WebSocket: {event}", extra=extra)
