from typing import Any, Dict
import logging
from src.domain.interfaces.connector_i import ConnectorI

class LogConnector(ConnectorI):
    def __init__(self, api_integrator):
        self.api = api_integrator
        
    def execute(self, command: str, data: Any, params: Dict) -> None:
        """Handle logging operations"""
        level = command.split('.')[1]
        if not isinstance(data, str):
            data = data.to_dict()
        message = self.api.render_template(data, params)
        getattr(logging, level)(message)
