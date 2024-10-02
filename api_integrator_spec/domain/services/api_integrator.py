import yaml
import json
import re
import requests
import logging
from pathlib import Path
from typing import Dict, Any, List, Union
from api_integrator_spec.domain.value_objects.yaml_object import YamlObject

class ApiIntegrator:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.vars = self.config.vars.to_dict() if hasattr(self.config, 'vars') else {}
        self.constants = self.config.constants.to_dict() if hasattr(self.config, 'constants') else {}
        self.session = requests.Session()
        self._setup_logging()

    def _load_config(self) -> YamlObject:
        with open(self.config_path) as f:
            return YamlObject(yaml.safe_load(f))

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def perform_action(self, action_name: str, params: Dict[str, Any] = None):
        action = self.config.actions.get(action_name)
        if not action:
            raise ValueError(f"Action '{action_name}' not found in config")

        merged_params = {**self.vars, **(params or {})}
        for perform in action.performs:
            self._execute_perform(perform, merged_params)

    def _execute_perform(self, perform: YamlObject, params: Dict[str, Any]):
        command = perform.perform
        data = perform.data if isinstance(perform.data, dict) else perform.data.to_dict() if hasattr(perform, 'data') else {}

        command_handlers = {
            'http.': self._handle_http_request,
            'log.': self._handle_log,
            'action.': self._handle_action,
            'vars.set': self._handle_vars_set,
            'vars.get': self._handle_vars_get
        }

        for prefix, handler in command_handlers.items():
            if command.startswith(prefix):
                handler(command, data, params)
                break
        else:
            raise ValueError(f"Unknown command: {command}")

        if hasattr(perform, 'responses'):
            self._handle_responses(perform.responses, params)

    def _handle_http_request(self, command: str, data: Dict[str, Any], params: Dict[str, Any]):
        method = command.split('.')[1].upper()
        url = self._render_template(data.get('path', ''), params)
        headers = {k: self._render_template(v, params) for k, v in data.get('headers', {}).items()}
        body = self._render_template(json.dumps(data.get('body', {})), params)
        query = {k: self._render_template(v, params) for k, v in data.get('query', {}).items()}

        response = self.session.request(method, url, headers=headers, data=body, params=query)
        params['response'] = ResponseWrapper(response)

    def _handle_log(self, command: str, data: Dict[str, Any], params: Dict[str, Any]):
        level = command.split('.')[1]
        message = self._render_template(data, params)
        getattr(logging, level)(message)

    def _handle_action(self, command: str, data: Dict[str, Any], params: Dict[str, Any]):
        action_name = command.split('.')[1]
        self.perform_action(action_name, params)

    def _handle_vars_set(self, data: Dict[str, Any], params: Dict[str, Any]):
        for key, value in data.items():
            self.vars[key] = self._render_template(value, params)

    def _handle_vars_get(self, data: Dict[str, Any], params: Dict[str, Any]):
        for key in data:
            params[key] = self.vars.get(key)

    def _handle_responses(self, responses: List[YamlObject], params: Dict[str, Any]):
        response_handlers = {
            'is_success': lambda r, p: self._check_response_conditions(r.is_success, p),
            'is_error': lambda r, p: hasattr(r, 'is_error') and self._check_response_conditions(r.is_error, p)
        }

        for response in responses:
            for condition, check in response_handlers.items():
                if check(response, params):
                    self._execute_performs(response.performs, params)
                    return

    def _check_response_conditions(self, conditions: YamlObject, params: Dict[str, Any]) -> bool:
        response = params['response']
        for condition, value in conditions:
            if condition == 'code' and response.status_code != value:
                return False
            elif condition == 'contains' and value not in response.text:
                return False
            elif condition == 'has_value' and not response.text:
                return False
            # Add more condition checks as needed
        return True

    def _execute_performs(self, performs: List[YamlObject], params: Dict[str, Any]):
        for perform in performs:
            self._execute_perform(perform, params)

    def _render_template(self, template: Union[str, Dict, List], params: Dict[str, Any]) -> Any:
        if isinstance(template, str):
            return re.sub(r'\{\{(.+?)\}\}', lambda m: str(self._get_value(m.group(1).strip(), params)), template)
        elif isinstance(template, dict):
            return {k: self._render_template(v, params) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._render_template(item, params) for item in template]
        else:
            return template

    def _get_value(self, key: str, params: Dict[str, Any]) -> Any:
        if key in params:
            return params[key]
        elif key in self.vars:
            return self.vars[key]
        elif key in self.constants:
            return self.constants[key]
        else:
            return f"{{{{ {key} }}}}"  # Leave unresolved variables as is

class ResponseWrapper:
    def __init__(self, response: requests.Response):
        self.response = response

    def __getattr__(self, name: str) -> Any:
        if name == 'body':
            return self.response.text
        elif name == 'json':
            return self.response.json()
        else:
            return getattr(self.response, name)

def main():
    config_path = 'api_integrator_spec/infrastructure/config/api_parser_conf.yml'
    integrator = ApiIntegrator(config_path)
    
    # Example usage
    integrator.perform_action('auth', {'user': 'testuser', 'pass': 'testpass'})
    integrator.perform_action('get_item_part', {'id_item': '123', 'id_part': '456'})

if __name__ == '__main__':
    main()
