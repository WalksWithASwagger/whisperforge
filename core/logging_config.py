"""
Enhanced Logging Configuration for WhisperForge
Provides structured logging with different levels and contexts
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
import json
import traceback
from typing import Dict, Any, Optional

class WhisperForgeLogger:
    """Enhanced logger with context and structured output"""
    
    def __init__(self, name: str = "whisperforge"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging with multiple handlers and formats"""
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set base level
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Console handler with color coding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            logs_dir / f"whisperforge_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Error handler for critical issues
        error_handler = logging.FileHandler(
            logs_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def log_pipeline_step(self, step: str, status: str, data: Optional[Dict] = None):
        """Log pipeline step with structured data"""
        log_data = {
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        
        if status == "started":
            self.logger.info(f"🔄 Pipeline step started: {step}")
        elif status == "completed":
            self.logger.info(f"✅ Pipeline step completed: {step}")
        elif status == "failed":
            self.logger.error(f"❌ Pipeline step failed: {step}")
            if data and "error" in data:
                self.logger.error(f"Error details: {data['error']}")
        
        # Log structured data to file
        self._log_structured(log_data)
    
    def log_file_upload(self, filename: str, size_mb: float, file_type: str):
        """Log file upload details"""
        self.logger.info(f"📁 File uploaded: {filename} ({size_mb:.1f}MB, {file_type})")
        self._log_structured({
            "event": "file_upload",
            "filename": filename,
            "size_mb": size_mb,
            "file_type": file_type,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_ai_request(self, provider: str, model: str, prompt_type: str, tokens: Optional[int] = None):
        """Log AI API requests"""
        self.logger.info(f"🤖 AI request: {provider}/{model} for {prompt_type}")
        self._log_structured({
            "event": "ai_request",
            "provider": provider,
            "model": model,
            "prompt_type": prompt_type,
            "tokens": tokens,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_database_operation(self, operation: str, table: str, success: bool, error: Optional[str] = None):
        """Log database operations"""
        status = "✅" if success else "❌"
        self.logger.info(f"{status} Database {operation}: {table}")
        if error:
            self.logger.error(f"Database error: {error}")
        
        self._log_structured({
            "event": "database_operation",
            "operation": operation,
            "table": table,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_user_action(self, action: str, user_id: Optional[str] = None, details: Optional[Dict] = None):
        """Log user actions"""
        self.logger.info(f"👤 User action: {action} (user: {user_id or 'anonymous'})")
        self._log_structured({
            "event": "user_action",
            "action": action,
            "user_id": user_id,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def log_error(self, error: Exception, context: Optional[str] = None):
        """Log errors with full context"""
        error_msg = str(error)
        error_type = type(error).__name__
        
        self.logger.error(f"💥 {error_type}: {error_msg}")
        if context:
            self.logger.error(f"Context: {context}")
        
        # Log full traceback
        self.logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        self._log_structured({
            "event": "error",
            "error_type": error_type,
            "error_message": error_msg,
            "context": context,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        })
    
    def _log_structured(self, data: Dict[str, Any]):
        """Log structured data to JSON file"""
        json_log_file = Path("logs") / f"structured_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        try:
            with open(json_log_file, "a") as f:
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write structured log: {e}")

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

# Global logger instance
logger = WhisperForgeLogger()

# Convenience functions
def log_pipeline_step(step: str, status: str, data: Optional[Dict] = None):
    logger.log_pipeline_step(step, status, data)

def log_file_upload(filename: str, size_mb: float, file_type: str):
    logger.log_file_upload(filename, size_mb, file_type)

def log_ai_request(provider: str, model: str, prompt_type: str, tokens: Optional[int] = None):
    logger.log_ai_request(provider, model, prompt_type, tokens)

def log_database_operation(operation: str, table: str, success: bool, error: Optional[str] = None):
    logger.log_database_operation(operation, table, success, error)

def log_user_action(action: str, user_id: Optional[str] = None, details: Optional[Dict] = None):
    logger.log_user_action(action, user_id, details)

def log_error(error: Exception, context: Optional[str] = None):
    logger.log_error(error, context) 