from pathlib import Path
from typing import Dict, List, Any
from src.domain.services.config_loader import ConfigLoader
from src.domain.services.template_engine import TemplateEngine
from src.domain.services.response_handler import ResponseHandler
from src.domain.services.connectors.http_connector import HttpConnector
from src.domain.services.connectors.web_connector import WebConnector
from src.domain.services.connectors.app_connector import AppConnector
from src.domain.services.connectors.log_connector import LogConnector
from src.domain.services.connectors.vars_connector import VarsConnector
from src.domain.value_objects.obj_utils import Obj

class Connector:
    def __init__(self, config_path: str):
        # Initialize core components
        self.config = ConfigLoader(config_path).load()
        self.response_handler = ResponseHandler()
        
        # Initialize connectors
        self.connectors = {
            'http': HttpConnector(self),
            'web': WebConnector(self),
            'app': AppConnector(self),
            'log': LogConnector(self),
            'vars': VarsConnector(self)
        }
        
        # Initialize template engine
        self.template_engine = TemplateEngine(
            self.connectors['vars'],
            self.response_handler
        )
        
        # Initialize vars and constants
        self.vars = self.config.vars if self.config.has('vars') else Obj({})
        self.constants = self.config.constants if self.config.has('constants') else Obj({})
        
    def perform_action(self, action_name: str, params: Obj = None):
        """Execute an action from configuration"""
        action = self.config.actions.get(action_name)
        if not action:
            raise ValueError(f"Action '{action_name}' not found")
            
        merged_params = self._merge_params(params)
        
        for perform in action.performs:
            self.execute_perform(perform, merged_params)
            
    def execute_perform(self, perform_info: Obj, params: Obj):
        """Execute a single perform directive"""
        action = perform_info.perform
        data = action.data if isinstance(action, Obj) and action.has('data') else Obj({})
        
        # Get action string
        action_str = action.action if isinstance(action, Obj) else action
        
        # Get connector type from action
        connector_type = action_str.split('.')[0]
        
        if connector_type not in self.connectors:
            raise ValueError(f"Unknown connector type: {connector_type}")
            
        # Render templates in data
        rendered_data = self.template_engine.render(data, params)
        
        # Execute via appropriate connector
        result = self.connectors[connector_type].execute(action_str, rendered_data, params)
        
        # Handle response if present
        if hasattr(result, 'response'):
            self.response_handler.set_response(result)
            
        # Handle response conditions if present
        if 'responses' in perform_info:
            self._handle_responses(perform_info.responses, params)
            
    def _merge_params(self, params: Obj = None) -> Obj:
        """Merge provided params with vars and constants"""
        return Obj({
            **(params.to_dict() if params else {}),
            **self.vars.to_dict(),
            **self.constants.to_dict()
        })
        
    def _handle_responses(self, responses: List[Obj], params: Obj):
        """Process response conditions and execute corresponding actions"""
        for response in responses:
            for condition_type in ['is_success', 'is_error']:
                if response.has(condition_type) and \
                   self.response_handler.check_conditions(response[condition_type]):
                    self._execute_response_performs(response.get('performs', []), params)
                    return
                    
    def _execute_response_performs(self, performs: List[Obj], params: Obj):
        """Execute performs for matching response condition"""
        for perform in performs:
            if perform.has('perform'):
                self.execute_perform(perform, params)

def main():
    config_relative_path = 'infrastructure/specs/api_integrator/cva_ai.yaml'
    connector = Connector(config_relative_path)
    for action_name, action_body in connector.config.actions.items():
        for perform in action_body.performs:
            if perform.perform.action == 'http.get':
                connector.perform_action(action_name)

if __name__ == '__main__':
    main()
