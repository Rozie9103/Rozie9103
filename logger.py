import logging
import os
from logging.handlers import RotatingFileHandler

# Define log levels mapping for easier access
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

def setup_logger(name="rozie", log_file="logs/rozie.log", level="INFO", 
                 max_size_mb=10, backup_count=5, console_output=True, 
                 format_str='%(asctime)s [%(levelname)s] %(name)s - %(message)s'):
    """
    Setup a logger with file and console handlers.
    
    Args:
        name (str): Logger name
        log_file (str): Path to log file
        level (str or int): Logging level (can be string like "INFO" or logging constant)
        max_size_mb (int): Maximum size of log file in MB before rotation
        backup_count (int): Number of backup files to keep
        console_output (bool): Whether to output logs to console
        format_str (str): Log format string
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Convert string level to logging constant if needed
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    logger.setLevel(level)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # File handler (with rotation)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Default application logger
logger = setup_logger()

def get_logger(module_name=None, level="INFO"):
    """
    Get a logger for a specific module with configurable level.
    
    Args:
        module_name (str, optional): Name of the module. If None, returns the root logger.
        level (str or int): Logging level (can be string like "INFO" or logging constant)
        
    Returns:
        logging.Logger: Logger for the specified module
    """
    if module_name:
        logger_name = f"rozie.{module_name}"
    else:
        logger_name = "rozie"
    
    logger = logging.getLogger(logger_name)
    
    # Convert string level to logging constant if needed
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    logger.setLevel(level)
    
    return logger

def get_toolkit_logger(level="INFO"):
    """
    Get a logger for Rozie Toolkit with configurable level.
    
    Args:
        level (str or int): Logging level (can be string like "INFO" or logging constant)
        
    Returns:
        logging.Logger: Logger for Rozie Toolkit
    """
    logger = logging.getLogger("rozie_toolkit")
    
    # Only add handlers if they don't exist yet
    if not logger.handlers:
        # Create formatter
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Convert string level to logging constant if needed
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    logger.setLevel(level)
    
    return logger
