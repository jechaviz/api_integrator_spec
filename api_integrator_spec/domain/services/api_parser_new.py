import os
import re
import ast
import json
import yaml
from chevron import render
from pathlib import Path
from api_integrator_spec.domain.value_objects.yaml_object import YamlObject

class ApiParserNew:
    def __init__(self, config_path: Path):
        self.config_path = self._create_path(config_path)
        self.api_name = self.config_path.stem
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
        try:
            action_template = self.action_templates[action_id]
        except KeyError:
            raise KeyError(f"Action '{action_id}' not found in config")
        merged_values = {**self.var_defaults, **values}
        action_str = render(str(action_template), merged_values)
        try:
            action = ast.literal_eval(action_str)
        except (SyntaxError, ValueError) as e:
            raise ValueError(f"Error parsing action '{action_id}': {e}")
        requests = []
        for item in action:
            payload = re.sub(r'"(\d+)"', r'\1', json.dumps(item['payload']))
            request = item['endpoint'].format(payload=payload)
            requests.append(request)
        return requests

    def generate_class(self):
        class_code = f'class {self.api_name.title().replace("_", "")}:'
        class_code += """
        def __init__(self, api_actions_config_file):
            self.api_parser = ApiParserNew(api_actions_config_file)
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


def print_action(api, action_id, values):
    print(action_id)
    requests = api.action_requests(action_id, values)
    for request in requests:
        print(request)
    print()


def main():
    values = {
        'asset': 'usd',
        'price': 5,
        'duration': 1,
        'direction': 2,
        'is_demo': 1
    }
    from pathlib import Path
    config_path = Path(__file__).resolve().parent.parent.parent / 'infrastructure' / 'config' / 'api_parser_conf.yml'
    api = ApiParserNew(config_path)
    class_code = api.generate_class()
    print(class_code)


if __name__ == '__main__':
    main()
    def _create_path(self, relative_path: Path) -> Path:
        return relative_path.resolve()
