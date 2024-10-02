import re
import ast
import json
import yaml
from chevron import render
from pathlib import Path
from api_integrator_spec.domain.value_objects.yaml_object import YamlObject

class ApiParserNew:
    def __init__(self, config_path: str):
        self.config_path = self._create_path(config_path)
        self.api_name = self.config_path.stem
        self.api = self._load_config()
        self.class_template = ''
        self.var_defaults = self.api.vars
        self.constants = self.api.constants

    def _load_config(self):
        with open(self.config_path) as f:
            data = yaml.safe_load(f)
            return YamlObject(data)

    def action_requests(self, action_id, values):
        try:
            action_data = self.api.actions.get(action_id)
            if not action_data:
                raise KeyError(f"Action '{action_id}' not found in config")
        except AttributeError:
            raise KeyError(f"Action '{action_id}' not found in config")

        merged_values = {**self.var_defaults.to_dict(), **values}
        requests = []

        for perform in action_data.performs:
            request = {
                'perform': perform.perform,
                'data': perform._data.to_dict() if hasattr(perform, 'data') else {},
                'responses': {}
            }

            if hasattr(perform, 'responses'):
                for response_type, response_data in perform.responses:
                    request['responses'][response_type] = response_data.to_dict()

            request_str = json.dumps(request)
            rendered_request = render(request_str, merged_values)
            try:
                parsed_request = json.loads(rendered_request)
                requests.append(parsed_request)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing request for action '{action_id}': {e}")

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
                payload = action_item._data.body
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

    @staticmethod
    def _create_path(relative_path: str) -> Path:
        return Path.cwd().parent.parent / relative_path


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
    api = ApiParserNew('infrastructure/config/api_parser_conf.yml')
    class_code = api.generate_class()
    print(class_code)


if __name__ == '__main__':
    main()
