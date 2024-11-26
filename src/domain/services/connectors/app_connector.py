from typing import Any, Dict
import importlib
import logging
from src.domain.interfaces.connector_i import ConnectorI

class AppConnector(ConnectorI):
    def __init__(self, api_integrator):
        self.api = api_integrator
        
    def execute(self, command: str, data: Any, params: Dict) -> Any:
        """Execute dynamic app method calls"""
        # Remove 'app.' prefix
        method_path = command[4:]
        
        try:
            # Split into module path and method name
            module_path, method_name = method_path.rsplit('.', 1)
            
            # Import module dynamically
            module = importlib.import_module(module_path)
            
            # Get and call method
            method = getattr(module, method_name)
            return method(data, params)
            
        except Exception as e:
            logging.error(f"Error executing app method {method_path}: {e}")
            raise
