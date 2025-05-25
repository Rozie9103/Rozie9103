import importlib
import os

def load_validators(validators_dir="validators"):
    validators = {}
    for fname in os.listdir(validators_dir):
        if fname.endswith(".py") and not fname.startswith("_"):
            modulename = fname[:-3]
            module = importlib.import_module(f"{validators_dir}.{modulename}")
            for attr in dir(module):
                if attr.startswith("validate_"):
                    validators[attr] = getattr(module, attr)
    return validators