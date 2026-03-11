"""
Centralized logging configuration for the application.
Provides structured logging for debugging and monitoring in production.
"""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Log directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log file paths
FRONTEND_LOG_FILE = LOG_DIR / "frontend.log"
REBUILD_LOG_FILE = LOG_DIR / "rebuild.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str,
    log_file: Path = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Setup a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Path to log file (optional)
        level: Logging level (default: INFO)
        console: Whether to log to console (default: True)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Error file handler (logs only errors and above)
    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


def get_frontend_logger() -> logging.Logger:
    """Get logger for frontend services."""
    return setup_logger("frontend", FRONTEND_LOG_FILE, logging.INFO)


def get_rebuild_logger() -> logging.Logger:
    """Get logger for rebuild operations."""
    return setup_logger("rebuild_manager", REBUILD_LOG_FILE, logging.INFO)


def get_core_logger(module_name: str) -> logging.Logger:
    """Get logger for core modules."""
    return setup_logger(f"core.{module_name}", None, logging.INFO)


def get_workflow_logger() -> logging.Logger:
    """Get logger for workflow operations."""
    return setup_logger("workflow", None, logging.INFO)


def get_vector_store_logger() -> logging.Logger:
    """Get logger for vector store operations."""
    return setup_logger("vector_store", None, logging.INFO)
