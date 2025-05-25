import os
import yaml
from dotenv import load_dotenv

def load_config_yaml(path="config.yaml"):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_env(path=".env"):
    if os.path.exists(path):
        load_dotenv(path)
    # Return as dict
    return dict(os.environ)