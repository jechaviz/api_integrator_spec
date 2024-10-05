import snoop
import yaml
import json
import re
import requests
import logging
from pathlib import Path
from typing import Dict, Any, List, Union
from src.domain.value_objects.yml_obj import YmlObj
from src.domain.value_objects.api_response import ApiResponse
from src.infrastructure.services.oas_parser.oas_parser_factory import OasParserFactory

class ApiIntegrator:
    def __init__(self, config_path: str, is_oas: bool = False):
        self.config_path = Path(__file__).resolve().parent.parent.parent / config_path
        self.config = self._load_config(is_oas)
        self.vars = self.config.vars if self.config.has('vars') else YmlObj({})
        self.constants = self.config.constants if self.config.has('constants') else YmlObj({})
        self.session = requests.Session()
        self.latest_response = None
        self._setup_logging()

    def _load_config(self, is_oas: bool) -> YmlObj:
        if is_oas:
            config_dict = OasParserFactory.create_and_map(str(self.config_path))
            return YmlObj(config_dict)
        else:
            with open(self.config_path) as f:
                return YmlObj(yaml.safe_load(f))

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def perform_action(self, action_name: str, params: YmlObj = None):
        action = self.config.actions.get(action_name)
        if not action:
            raise ValueError(f"Action '{action_name}' not found in config")

        merged_params = YmlObj({**self.vars.to_dict(), **self.constants.to_dict(), **(params.to_dict() if params else {})})
        logging.debug(f"Performing action '{action_name}' with params: {merged_params}")
        for perform in action.performs:
            self.execute_perform(perform, merged_params)

    def execute_perform(self, perform_info: YmlObj, params: YmlObj):
        command = perform_info.perform
        data = command.data if command.has('data') else YmlObj({})

        logging.debug(f"Executing command: {command}")
        logging.debug(f"Command data: {data}")
        logging.debug(f"Params: {params}")

        if isinstance(command, YmlObj):
            command_str = command.a
        elif isinstance(command, str):
            command_str = command
        else:
            raise ValueError(f"Invalid command type: {type(command)}")

        command_parts = command_str.split('.')
        if len(command_parts) > 1:
            handler_name = f'_handle_{command_parts[0]}'
            handler = getattr(self, handler_name, None)
            if handler:
                handler(command_str, data, params)
            else:
                raise ValueError(f"Unknown command: {command_str}")
        else:
            raise ValueError(f"Invalid command format: {command_str}")

        if perform_info.has('responses'):
            self._handle_responses(perform_info.responses, params)

    def _handle_http(self, command: str, data: YmlObj, params: YmlObj):
        method = command.split('.')[1].upper()
        endpoint = data.get('path', '')
        url = self.render_template(endpoint, params)
        headers = YmlObj({k: self.render_template(v, params) for k, v in data.get('headers', YmlObj({})).items()})
        body_data = data.get('body', YmlObj({}))
        body = self.render_template(json.dumps(body_data.to_dict()), params)
        query = YmlObj({k: self.render_template(v, params) for k, v in data.get('query', YmlObj({})).items()})

        logging.debug(f"HTTP Request: {method} {url}")
        logging.debug(f"Headers: {headers}")
        logging.debug(f"Body: {body}")
        logging.debug(f"Query: {query}")

        response = self.session.request(method, url, headers=headers.to_dict(), data=body, params=query.to_dict())
        api_response = ApiResponse(response)
        params['response'] = api_response
        self.latest_response = api_response
        self.vars['response'] = api_response

        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response content: {response.text[:200]}...")  # Log first 200 characters of response

    def _handle_log(self, command: str, data: YmlObj, params: YmlObj):
        level = command.split('.')[1]
        if not(isinstance(data, str)):
            data = data.to_dict()
        message = self.render_template(data, params)
        getattr(logging, level)(message)

    def _handle_action(self, command: str, data: YmlObj, params: YmlObj):
        action_name = command.split('.')[1]
        self.perform_action(action_name, params)

    def _handle_vars(self, command: str, data: YmlObj, params: YmlObj):
        operation = command.split('.')[1]
        if operation == 'set':
            for key, value in data.items():
                self.vars[key] = self.render_template(value, params)
        elif operation == 'get':
            for key in data:
                params[key] = self.vars.get(key)
        else:
            raise ValueError(f"Unknown vars operation: {operation}")

    def _handle_responses(self, responses: List[YmlObj], params: YmlObj):
        for response in responses:
            for condition_type in ['is_success', 'is_error']:
                if response.has(condition_type) and self._check_response_conditions(response[condition_type], params):
                    self._execute_performs(response.performs, params)
                    return

        logging.warning("No matching response conditions found")

    def _check_response_conditions(self, conditions: YmlObj, params: YmlObj) -> bool:
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

    def _execute_performs(self, performs: List[YmlObj], params: YmlObj):
        for perform in performs:
            self.execute_perform(perform, params)

    def render_template(self, template: Union[str, YmlObj, List], params: YmlObj) -> Any:
        if isinstance(template, str):
            result = re.sub(r'\{\{(.+?)\}\}', lambda m: self.render_value(m.group(1).strip(), params), template)
            logging.debug(f"Rendered template: {template} -> {result}")
            return result
        elif isinstance(template, YmlObj):
            return YmlObj({k: self.render_template(v, params) for k, v in template.items()})
        elif isinstance(template, list):
            return [self.render_template(item, params) for item in template]
        return template

    def render_value(self, key: str, params: YmlObj) -> str:
        value = self.get_value(key, params)
        if isinstance(value, dict):
            return json.dumps(value)
        return str(value)

    def get_value(self, key: str, params: YmlObj) -> Any:
        if key.startswith('response.'):
            response_key = key[9:]  # Remove 'response.' prefix
            if self.latest_response:
                if response_key == 'json':
                    return self.latest_response.body
                elif hasattr(self.latest_response, response_key):
                    return getattr(self.latest_response, response_key)
                else:
                    logging.warning(f"Unknown response attribute: {response_key}")
                    return f"{{{{ {key} }}}}"
            else:
                logging.warning(f"No response available for key: {key}")
                return f"{{{{ {key} }}}}"

        if key == 'supplier_server.url':
            supplier_server = params.get('supplier_server') or self.vars.get('supplier_server') or self.constants.get('supplier_server')
            if isinstance(supplier_server, YmlObj):
                if supplier_server.has('url'):
                    return supplier_server.url
                elif supplier_server.has('id'):
                    server_id = supplier_server.id
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
    config_path = 'infrastructure/config/jsonplaceholder_conf.yml'
    integrator = ApiIntegrator(config_path)
    
    # Example usage
    integrator.perform_action('get_all_users')
    #integrator.perform_action('get_item_part', YmlObj({'id_item': '123', 'id_part': '456'}))

    # Example usage with OAS file
    oas_path = 'path/to/your/oas_file.yaml'
    oas_integrator = ApiIntegrator(oas_path, is_oas=True)
    # Perform actions based on the mapped OAS specification
    oas_integrator.perform_action('get_users')

if __name__ == '__main__':
    main()
