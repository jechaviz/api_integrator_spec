from typing import Any, Dict
import logging
from src.domain.interfaces.connector_i import ConnectorI

class VarsConnector(ConnectorI):
    def __init__(self, api_integrator):
        self.api = api_integrator
        
    def execute(self, command: str, data: Any, params: Dict) -> None:
        """Handle variable operations"""
        operation = command.split('.')[1]
        if operation == 'set':
            for key, value in data.items():
                rendered_value = self.api.render_template(value, params)
                if rendered_value != value:
                    self.api.vars[key] = rendered_value
                    logging.info(f'Updated var {key}={rendered_value}')
        elif operation == 'get':
            for key in data:
                params[key] = self.api.vars.get(key)
        else:
            raise ValueError(f'Unknown vars operation: {operation}')
