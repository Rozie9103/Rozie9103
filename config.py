import json
import os
from typing import Dict, Any, Optional

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file (default: config.json)
        
    Returns:
        Dictionary containing configuration values or empty dict if file doesn't exist
    """
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: {config_path} contains invalid JSON")
            return {}
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return {}
    return {}

def save_config(config_data: Dict[str, Any], config_path: str = "config.json") -> bool:
    """
    Save configuration to a JSON file.
    
    Args:
        config_data: Dictionary containing configuration to save
        config_path: Path to save the configuration file (default: config.json)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {str(e)}")
        return False

def get_config_value(key: str, default: Any = None, config_path: str = "config.json") -> Any:
    """
    Get a specific value from the configuration.
    
    Args:
        key: Configuration key to retrieve
        default: Default value if key doesn't exist
        config_path: Path to the configuration file
        
    Returns:
        Value for the specified key or default if not found
    """
    config = load_config(config_path)
    return config.get(key, default)

def update_config_value(key: str, value: Any, config_path: str = "config.json") -> bool:
    """
    Update a specific value in the configuration.
    
    Args:
        key: Configuration key to update
        value: New value to set
        config_path: Path to the configuration file
        
    Returns:
        True if successful, False otherwise
    """
    config = load_config(config_path)
    config[key] = value
    return save_config(config, config_path)
