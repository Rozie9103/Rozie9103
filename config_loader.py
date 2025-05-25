import os
import yaml
import json
from pathlib import Path

def load_config(config_path="config/default.yaml", env_prefix="APP_"):
    """
    Load configuration from YAML or JSON file with environment variable override support.
    
    Args:
        config_path (str): Path to the configuration file
        env_prefix (str): Prefix for environment variables to override config values
        
    Returns:
        dict: Configuration dictionary
    """
    # Check if file exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load configuration based on file extension
    if config_path.endswith(".yaml") or config_path.endswith(".yml"):
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {config_path}: {str(e)}")
    elif config_path.endswith(".json"):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {config_path}: {str(e)}")
    else:
        raise ValueError(f"Unsupported config file format: {config_path}")
    
    # Override with environment variables if they exist
    if config:
        _override_from_env(config, env_prefix)
    
    return config

def _override_from_env(config, prefix, path=""):
    """
    Recursively override configuration values with environment variables.
    
    Environment variables should be in the format:
    {PREFIX}_{PATH}_{KEY} (all uppercase with underscores)
    """
    for key, value in config.items():
        env_path = f"{path}_{key}" if path else key
        env_var = f"{prefix}{env_path}".upper().replace(".", "_")
        
        if isinstance(value, dict):
            _override_from_env(value, prefix, env_path)
        else:
            if env_var in os.environ:
                # Convert environment variable to appropriate type
                env_value = os.environ[env_var]
                if isinstance(value, bool):
                    config[key] = env_value.lower() in ('true', 'yes', '1')
                elif isinstance(value, int):
                    config[key] = int(env_value)
                elif isinstance(value, float):
                    config[key] = float(env_value)
                else:
                    config[key] = env_value

def create_default_config(config_path="config/default.yaml", config_format="yaml"):
    """
    Create a default configuration file if it doesn't exist.
    
    Args:
        config_path (str): Path to create the configuration file
        config_format (str): Format of the configuration file ('yaml' or 'json')
    """
    if os.path.exists(config_path):
        return
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # Default configuration
    default_config = {
        "app": {
            "name": "MyApp",
            "debug": False
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "username": "user",
            "password": "password",
            "name": "mydb"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/app.log"
        }
    }
    
    # Write configuration file
    if config_format.lower() in ("yaml", "yml"):
        with open(config_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)
    elif config_format.lower() == "json":
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=2)
    else:
        raise ValueError(f"Unsupported config format: {config_format}")
