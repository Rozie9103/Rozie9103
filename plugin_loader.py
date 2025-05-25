import os
import importlib
from abc import ABC, abstractmethod

class PluginBase(ABC):
    @abstractmethod
    def run(self, *args, **kwargs):
        pass

def discover_plugins(plugin_folder="plugins"):
    plugins = []
    folder_path = os.path.join(os.path.dirname(__file__), "..", plugin_folder)
    for fname in os.listdir(folder_path):
        if fname.endswith(".py") and not fname.startswith("__"):
            module_name = f"{plugin_folder}.{fname[:-3]}"
            module = importlib.import_module(module_name)
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, PluginBase) and obj is not PluginBase:
                    plugins.append(obj())
    return plugins