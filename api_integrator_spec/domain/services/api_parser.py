import re
import ast
import json
import yaml
from chevron import render
from api_integrator_spec.domain.value_objects.yaml_object import YamlObject
from api_integrator_spec.application.services.action_service import ActionService

class ApiParser:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.api_name = config_path.replace('.yml', '')
        self.api = self._load_config()
        self.action_templates = self._load_action_templates()
        self.class_template = ''
        self.var_defaults = self.api.vars
        self.constants = self.api.constants
        self.action_service = ActionService(self)
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.api_name = config_path.replace('.yml', '')
        self.api = self._load_config()
        self.action_templates = self._load_action_templates()
        self.class_template = ''
        self.var_defaults = self.api.vars
        self.constants = self.api.constants

    def _load_config(self):
        with open(self.config_path) as f:
            data = yaml.safe_load(f)
            return YamlObject(data)

    def _load_action_templates(self):
        request_templates = {}
        for action_name, action_items in self.api.actions.items():
            requests = []
            if not action_items: continue
            for action_item in action_items.performs:
                endpoint = action_item.data.path
                payload = action_item.data.body
                response_ok_contains = ''
                response_error_contains = ''
                try:
                    response_ok_contains = action_item.responses[0].is_success.contains
                    response_error_contains = action_item.responses[0].is_error.contains
                except:
                    pass
                requests.append({'endpoint': endpoint, 'payload': payload,
                                 'response_ok_contains': response_ok_contains,
                                 'response_error_contains': response_error_contains})
            request_templates[f'{action_name}'] = requests
        return request_templates

    def action_requests(self, action_id, values):
        return self.action_service.perform_action(action_id, values)

    def generate_class(self):
        class_code = f'class {self.api_name.title().replace("_", "")}:'
        class_code += """
        def __init__(self, api_actions_config_file):
            self.api_parser = ApiParser(api_actions_config_file)
            self.ws = None

        def send(self, action_id, params):
            if self.ws:
                try:
                    requests = self.api_parser.action_requests(action_id, params)
                    try:
                        for request in requests:
                            self.ws.send(request)
                            time.sleep(0.1)
                    except WebSocketException as wse:
                        print(wse)
                except Exception as e:
                    print(e)
        """
        for action_name, action_items in self.api.actions.items():
            keys = []
            for action_item in action_items.performs:
                payload = action_item.data.body
                keys.extend(self._get_template_keys(payload))
            arguments = ", ".join(keys)
            params = ", ".join([f"'{key}'={key}" for key in keys])
            method_code = f'\n  def {action_name}(self, {arguments}):'
            method_body = '\n    params = {' + f'{params}' + '}'
            method_body += f"\n    self.send('{action_name}', params)"
            method_code += method_body
            class_code += method_code + '\n'
        return class_code

    def _get_template_keys(self, data):
        keys = []
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and "{{" in value:
                    keys.append(re.sub(r'[\{\}]', '', value))
                else:
                    keys.extend(self._get_template_keys(value))
        return keys


