"""
Logging utility for InG AI Sales Department.
Standard Python logging with multiprocessing support via QueueHandler/QueueListener.
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from multiprocessing import Queue
import colorlog
import atexit

# Shared queue and listener (initialized automatically)
_log_queue = None
_log_listener = None

def setup_logger(name: str = "ing_agents", log_level: str = None, log_queue: Queue = None) -> logging.Logger:
    """
    Setup logger with file and console handlers.
    Automatically handles multiprocessing via QueueHandler if queue is provided.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_queue: Optional multiprocessing.Queue. If provided, uses QueueHandler for multiprocessing safety.
    
    Returns:
        Configured logger instance
    """
    global _log_queue, _log_listener
    
    # Get log level from environment
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers.clear()
    
    # Create logs directory
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Common formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Use queue if provided (multiprocessing mode)
    queue_to_use = log_queue or _log_queue
    
    if queue_to_use is not None:
        # Multiprocessing mode: use QueueHandler
        queue_handler = QueueHandler(queue_to_use)
        queue_handler.setLevel(logging.DEBUG)
        logger.addHandler(queue_handler)
        
        # Initialize listener in main process only (first call with queue)
        if _log_listener is None:
            log_file = log_dir / "agents.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                delay=True
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            
            console_handler = colorlog.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)
            
            _log_listener = QueueListener(queue_to_use, file_handler, console_handler, respect_handler_level=True)
            _log_listener.start()
            atexit.register(_stop_log_listener)
    else:
        # Single process mode: direct handlers
        log_file = log_dir / "agents.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            delay=True
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler (always direct for immediate output)
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

def _stop_log_listener():
    """Stop the log listener (internal, called via atexit)"""
    global _log_listener
    if _log_listener is not None:
        _log_listener.stop()
        _log_listener = None
