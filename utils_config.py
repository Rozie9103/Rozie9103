"""
Utility Configuration Module

This module provides utilities for console output, logging, and validation.
"""
import re
import os
import json
import platform
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.logging import RichHandler

# ===== Application Configuration =====
VERSION = "2.0"

# System information
SYSTEM_INFO = {
    "os": platform.system(),
    "os_version": platform.version(),
    "python_version": platform.python_version()
}

# ===== Console Configuration =====
# Custom theme for rich console
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "highlight": "bold magenta"
})

# Global console configuration
console = Console(theme=custom_theme)

def load_config(config_path="config.json"):
    """
    Load configuration from a JSON file.
    
    Args:
        config_path (str): Path to the configuration file (default: config.json)
        
    Returns:
        dict: Configuration data or empty dict if file doesn't exist
    """
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print_error(f"Error parsing config file: {config_path}")
            return {}
    return {}

def print_info(message):
    """Print an info message to the console"""
    console.print(f"[info]{message}[/info]")

def print_warning(message):
    """Print a warning message to the console"""
    console.print(f"[warning]{message}[/warning]")

def print_error(message):
    """Print an error message to the console"""
    console.print(f"[danger]{message}[/danger]")

def print_success(message):
    """Print a success message to the console"""
    console.print(f"[success]{message}[/success]")

def create_progress_bar():
    """Create a standard progress bar"""
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )

# ===== Logging Configuration =====
def setup_logging(log_level=logging.INFO, log_file=None):
    """Configure logging with Rich handler"""
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)]
    )
    
    # Add file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(file_handler)
    
    return logging.getLogger()

def setup_rotating_logging(log_level=logging.INFO, log_file=None, max_bytes=2*1024*1024, backup_count=5):
    """
    Configure logging with Rich handler and rotating file handler
    
    Args:
        log_level (int): Logging level (default: logging.INFO)
        log_file (str): Path to log file (default: None)
        max_bytes (int): Maximum size of log file before rotation in bytes (default: 2MB)
        backup_count (int): Number of backup files to keep (default: 5)
        
    Returns:
        logger: Configured logger instance
    """
    handlers = [RichHandler(rich_tracebacks=True, console=console)]
    
    # Add rotating file handler if log_file is specified
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
        force=True
    )
    
    return logging.getLogger()

# ===== Password Validation =====
COMMON_PASSWORDS = [
    "password", "123456", "123456789", "qwerty", "abc123", "password1", "111111", "123123", "admin", "letmein",
    "welcome", "monkey", "login", "princess", "dragon", "sunshine", "rahasia123", "indonesia", "bismillah",
    "sayang", "anjing", "kontol", "12345678", "qwertyuiop", "jakarta", "bandung", "bajingan", "pancasila",
    "merdeka", "kucing", "doraemon", "bajigur"
]

KEYBOARD_WALKS = [
    "qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890", "1q2w3e4r", "qazwsx", "poiuytrewq"
]

LEET_SPEAK_MAP = {
    "a": ["4", "@"],
    "e": ["3"],
    "i": ["1", "!"],
    "o": ["0"],
    "s": ["5", "$"],
    "t": ["7"],
    "b": ["8"]
}

SPECIAL_COMBINATIONS = [
    "!", "@", "#", "$", "%", "&", "*", "2024", "123", "321", "007"
]

def validate_password_strength(password, min_length=8):
    """
    Validate password strength
    
    Args:
        password (str): Password to validate
        min_length (int): Minimum password length
        
    Returns:
        tuple: (is_valid, message)
    """
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    if password.lower() in COMMON_PASSWORDS:
        return False, "Password is too common"
    
    for walk in KEYBOARD_WALKS:
        if walk in password.lower():
            return False, "Password contains keyboard pattern"
    
    # Check for complexity
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    if not (has_upper and has_lower and has_digit and has_special):
        return False, "Password must contain uppercase, lowercase, digit, and special characters"
    
    return True, "Password meets strength requirements"

# ===== Input Validation =====
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, "Valid email format"
    return False, "Invalid email format"

def validate_phone_number(phone):
    """Validate phone number format"""
    # Basic pattern for international phone numbers
    pattern = r'^\+?[0-9]{10,15}$'
    if re.match(pattern, phone):
        return True, "Valid phone number format"
    return False, "Invalid phone number format"
