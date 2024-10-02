import snoop
import yaml
import json
import re
import requests
import logging
from pathlib import Path
from typing import Dict, Any, List, Union
from api_integrator_spec.domain.value_objects.yaml_object import YamlObject
from api_integrator_spec.domain.value_objects.api_response import ApiResponse

class ApiIntegrator:
    def __init__(self, config_path: str):
        self.config_path = Path.cwd().parent.parent / config_path
        self.config = self._load_config()
        self.vars = self.config.vars if self.config.has('vars') else YamlObject({})
        self.constants = self.config.constants if self.config.has('constants') else YamlObject({})
        self.session = requests.Session()
        self._setup_logging()

    def _load_config(self) -> YamlObject:
        with open(self.config_path) as f:
            return YamlObject(yaml.safe_load(f))

    def _setup_logging(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    @snoop
    def perform_action(self, action_name: str, params: Dict[str, Any] = None):
        action = self.config.actions.get(action_name)
        if not action:
            raise ValueError(f"Action '{action_name}' not found in config")

        merged_params = {**self.vars.to_dict(), **self.constants.to_dict(), **(params or {})}
        logging.debug(f"Performing action '{action_name}' with params: {merged_params}")
        for perform in action.performs:
            self.execute_perform(perform, merged_params)

    @snoop
    def execute_perform(self, perform: YamlObject, params: Dict[str, Any]):
        command = perform.perform
        data = perform.data if perform.has('data') else YamlObject({})

        logging.debug(f"Executing command: {command}")
        logging.debug(f"Command data: {data}")
        logging.debug(f"Params: {params}")

        command_parts = command.split('.')
        if len(command_parts) > 1:
            handler_name = f'_handle_{command_parts[0]}'
            handler = getattr(self, handler_name, None)
            if handler:
                handler(command, data, params)
            else:
                raise ValueError(f"Unknown command: {command}")
        else:
            raise ValueError(f"Invalid command format: {command}")

        if perform.has('responses'):
            self._handle_responses(perform.responses, params)

    @snoop
    def _handle_http(self, command: str, data: YamlObject, params: Dict[str, Any]):
        method = command.split('.')[1].upper()
        url = self.render_template(data.get('path', ''), params)
        headers = {k: self.render_template(v, params) for k, v in data.get('headers', YamlObject({})).items()}
        body = self.render_template(json.dumps(data.get('body', YamlObject({})).to_dict()), params)
        query = {k: self.render_template(v, params) for k, v in data.get('query', YamlObject({})).items()}

        logging.debug(f"HTTP Request: {method} {url}")
        logging.debug(f"Headers: {headers}")
        logging.debug(f"Body: {body}")
        logging.debug(f"Query: {query}")

        response = self.session.request(method, url, headers=headers, data=body, params=query)
        params['response'] = ApiResponse(response)

        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response content: {response.text[:200]}...")  # Log first 200 characters of response

    def _handle_log(self, command: str, data: YamlObject, params: Dict[str, Any]):
        level = command.split('.')[1]
        message = self.render_template(data.to_dict(), params)
        getattr(logging, level)(message)

    def _handle_action(self, command: str, data: YamlObject, params: Dict[str, Any]):
        action_name = command.split('.')[1]
        self.perform_action(action_name, params)

    def _handle_vars(self, command: str, data: YamlObject, params: Dict[str, Any]):
        operation = command.split('.')[1]
        if operation == 'set':
            for key, value in data.items():
                self.vars[key] = self.render_template(value, params)
        elif operation == 'get':
            for key in data:
                params[key] = self.vars.get(key)
        else:
            raise ValueError(f"Unknown vars operation: {operation}")

    def _handle_responses(self, responses: List[YamlObject], params: Dict[str, Any]):
        response_handlers = {
            'is_success': lambda r, p: self._check_response_conditions(r.is_success, p),
            'is_error': lambda r, p: r.has('is_error') and self._check_response_conditions(r.is_error, p)
        }

        for response in responses:
            for condition, check in response_handlers.items():
                if check(response, params):
                    self._execute_performs(response.performs, params)
                    return

    def _check_response_conditions(self, conditions: YamlObject, params: Dict[str, Any]) -> bool:
        response = params['response']
        condition_checks = {
            'code': lambda v: response.status_code == v,
            'contains': lambda v: v in response.text,
            'has_value': lambda v: bool(response.text) == v,
            'matches': lambda v: re.search(v, response.text) is not None,
            'has_key': lambda v: v in response.json(),
            'has_keys': lambda v: all(key in response.json() for key in v),
            'is_empty': lambda v: len(response.text) == 0 if v else len(response.text) > 0,
            'is_null': lambda v: response.text == 'null' if v else response.text != 'null',
            'is_type': lambda v: isinstance(response.json(), eval(v)),
            'length': lambda v: len(response.text) == v,
            'length_gt': lambda v: len(response.text) > v,
            'length_lt': lambda v: len(response.text) < v,
            'length_gte': lambda v: len(response.text) >= v,
            'length_lte': lambda v: len(response.text) <= v,
        }
        return all(condition_checks.get(condition, lambda v: False)(value) for condition, value in conditions.items())

    def _execute_performs(self, performs: List[YamlObject], params: Dict[str, Any]):
        for perform in performs:
            self.execute_perform(perform, params)

    @snoop
    def render_template(self, template: Union[str, Dict, List], params: Dict[str, Any]) -> Any:
        if isinstance(template, str):
            result = re.sub(r'\{\{(.+?)\}\}', lambda m: str(self.get_value(m.group(1).strip(), params)), template)
            logging.debug(f"Rendered template: {template} -> {result}")
            return result
        elif isinstance(template, dict):
            return {k: self.render_template(v, params) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.render_template(item, params) for item in template]
        return template

    def get_value(self, key: str, params: Dict[str, Any]) -> Any:
        if key == 'supplier_server.url':
            supplier_server = params.get('supplier_server') or self.vars.get('supplier_server') or self.constants.get('supplier_server')
            if isinstance(supplier_server, dict):
                if 'url' in supplier_server:
                    return supplier_server['url']
                elif 'id' in supplier_server:
                    server_id = supplier_server['id']
                    for server in self.config.supplier_servers:
                        if server.id == server_id:
                            return server.url
            elif isinstance(supplier_server, str):
                for server in self.config.supplier_servers:
                    if server.id == supplier_server:
                        return server.url
            logging.warning(f"Could not find supplier_server.url for {supplier_server}")
            return f"{{{{ supplier_server.url }}}}"
        
        value = params.get(key) or self.vars.get(key) or self.constants.get(key) or f"{{{{ {key} }}}}"
        logging.debug(f"Getting value for key '{key}': {value}")
        return value

def main():
    config_path = 'infrastructure/config/api_parser_conf.yml'
    integrator = ApiIntegrator(config_path)
    
    # Example usage
    integrator.perform_action('auth')
    integrator.perform_action('get_item_part', {'id_item': '123', 'id_part': '456'})

if __name__ == '__main__':
    main()
