import logging
import sys


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
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
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

