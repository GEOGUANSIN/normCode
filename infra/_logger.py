import logging
import sys


def get_utf8_stream(stream):
    """
    Get a stream configured for UTF-8 encoding.
    
    On Windows, the console uses cp1252 by default which can't handle Chinese
    and other Unicode characters. This reconfigures the stream for UTF-8 encoding
    with error handling to prevent encoding crashes.
    
    Args:
        stream: The stream to configure (usually sys.stdout or sys.stderr)
        
    Returns:
        The stream (reconfigured in place on Windows)
    """
    if sys.platform == "win32":
        # Use reconfigure() to safely change encoding without replacing streams
        # This avoids "I/O operation on closed file" errors
        try:
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # Silently ignore if configuration fails
            pass
    return stream


def setup_logging(level=logging.INFO, log_file=None):
    """Setup logging configuration for the inference module"""
    # Create formatter
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    # )
    formatter = logging.Formatter(
        '[%(levelname)s] %(message)s - %(asctime)s - %(name)s'
    )

    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler with UTF-8 encoding for Windows compatibility
    console_handler = logging.StreamHandler(get_utf8_stream(sys.stdout))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional) with UTF-8 encoding
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def set_infra_log_level(level: int = logging.INFO):
    """Set log level for all infra loggers. Use logging.DEBUG for verbose output."""
    for name in ['infra', 'infra._core', 'infra._agent', 'infra._orchest', 'infra._loggers']:
        logging.getLogger(name).setLevel(level)


# Don't auto-configure logging on import - let the application control logging
# setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Default to INFO, not DEBUG

