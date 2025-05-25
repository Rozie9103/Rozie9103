import logging
import json
from datetime import datetime
from cryptography.fernet import Fernet
from logging.handlers import RotatingFileHandler
from utils_config import console

def get_logger(
    name="rozie_toolkit",
    level="INFO",
    log_file=None,
    max_bytes=2*1024*1024,
    backup_count=5,
    rich_console=True
):
    """
    Returns a configured logger instance that can be used throughout the application.
    Supports console, file, and rotating file logging.
    
    Args:
        name (str): Logger name
        level (str): Logging level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
        log_file (str): Optional file path for file logging
        max_bytes (int): Maximum log file size before rotation
        backup_count (int): Number of backup files to keep
        rich_console (bool): Whether to use Rich for console output if available
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level if isinstance(level, int) else getattr(logging, level.upper(), logging.INFO))

    # Remove duplicate handlers if re-init
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler (with Rich if available)
    if rich_console:
        try:
            from rich.logging import RichHandler
            handler = RichHandler(rich_tracebacks=True, console=console)
        except ImportError:
            handler = logging.StreamHandler()
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)

    # File handler (rotating)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    return logger

class AttackLogger:
    """
    Advanced AttackLogger: 
    - Modular, support rotasi log, 
    - Kunci enkripsi bisa eksternal, 
    - Logging ke console & file, 
    - Siap integrasi plugin.
    """
    def __init__(
        self, 
        log_file="rozie_attack.log", 
        results_file="attack_results.log", 
        encrypted_file="attack_results.enc",
        encryption_key=None,
        log_level="INFO"
    ):
        self.logger = get_logger(
            name="RozieBruteForce",
            level=log_level,
            log_file=log_file,
            rich_console=True
        )
        self.results_file = results_file
        self.encrypted_file = encrypted_file
        # Kunci enkripsi bisa diberikan dari luar (misal: env/config) atau generate baru
        if encryption_key is None:
            self.encryption_key = Fernet.generate_key()
        else:
            self.encryption_key = encryption_key
        self.cipher = Fernet(self.encryption_key)
    
    def log_result(self, target_info, username, password, response):
        status_code = response.status_code if response else '-'
        target_url = target_info.get('target_url', 'Unknown')
        self.logger.info(f"SUCCESS: {username}:{password} @ {target_url} [{status_code}]")

        log_data = {
            'timestamp': str(datetime.now()),
            'target': target_url,
            'username': username,
            'password': password,
            'response_code': status_code,
            'response_preview': response.text[:200] if response and hasattr(response, "text") and response.text else ''
        }

        # Save plain text
        try:
            with open(self.results_file, 'a', encoding="utf-8") as f:
                f.write(f"{datetime.now()} - TARGET: {target_url} - CREDS: {username}:{password} - STATUS: {status_code}\n")
        except Exception as e:
            self.logger.warning(f"Failed to write plain result log: {e}")

        # Save encrypted version
        try:
            encrypted_log = self._encrypt_data(json.dumps(log_data))
            with open(self.encrypted_file, 'ab') as f:
                f.write(encrypted_log + b'\n')
        except Exception as e:
            self.logger.warning(f"Failed to write encrypted result log: {e}")
    
    def log_error(self, message):
        self.logger.error(f"ERROR: {message}")
        try:
            console.print(f"[red]Error: {message}[/red]")
        except Exception:
            print(f"Error: {message}")
    
    def log_attempt(self, username, password, details):
        """
        Log setiap percobaan brute force.
        """
        try:
            self.logger.info(f"ATTEMPT: username={username}, password={password}, details={details}")
            with open(self.results_file, 'a', encoding="utf-8") as f:
                f.write(f"{datetime.now()} - ATTEMPT: username={username}, password={password}, details={details}\n")
        except Exception as e:
            try:
                console.print(f"[yellow]Warning: Failed to log attempt: {e}[/yellow]")
            except Exception:
                print(f"Warning: Failed to log attempt: {e}")
    
    def _encrypt_data(self, data):
        return self.cipher.encrypt(data.encode())
    
    def get_encryption_key(self):
        """Return the encryption key (for saving to config/env if needed)"""
        return self.encryption_key
    
    def set_encryption_key(self, key):
        """Set a new encryption key (for loading from config/env)"""
        self.encryption_key = key
        self.cipher = Fernet(self.encryption_key)
