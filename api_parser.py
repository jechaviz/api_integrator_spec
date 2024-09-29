import re
import ast
import json

import yaml
from chevron import render


class ApiParser:
  # Defines an api in a yml per defined actions.
  # See api_parser_conf.yml.
  def __init__(self, config_path: str):
    self.config_path = config_path
    self.api_name = config_path.replace('.yml', '')
    self.api = self._load_config()
    self.action_templates = self._load_action_templates()
    self.class_template = ''
    self.var_defaults = self.api.get('var_defaults', {})
    self.constants = self.api.get('constants', {})

  def _load_config(self):
    with open(self.config_path) as f:
      return yaml.safe_load(f)

  def _load_action_templates(self):
    # load the templates to cache self.action_templates
    request_templates = {}
    for section, sections in self.api.items():
      if section != 'actions': continue
      for action_name, action_items in sections.items():
        requests = []
        if not action_items: continue
        for supplier_path in action_items['supplier_paths']:
          endpoint = supplier_path['path']
          payload = supplier_path.get('request', {}).get('body', {})
          responses = supplier_path.get('responses', [])
          response_ok_contains = ''
          response_error_contains = ''
          for response in responses:
            if response.get('code') == '200':
              response_ok_contains = response.get('contains', '')
            elif response.get('code') == '400':
              response_error_contains = response.get('contains', '')
          requests.append({'endpoint': endpoint, 'payload': payload,
                           'response_ok_contains': response_ok_contains,
                           'response_error_contains': response_error_contains})
        request_templates[f'{action_name}'] = requests
    return request_templates

  def action_requests(self, action_id, values):
    # fill the action template with values provided
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

  # TODO: define self.send. Sample in ws_default_client.send(action_id, params).
  def generate_class(self):
    class_code = f'class {self.api_name.title().replace('_', '')}:'
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
    for action_name, action_items in self.api['actions'].items():
      keys = []
      for action_item in action_items:
        payload = action_item.get('payload', {})
        keys.extend(self._get_template_keys(payload))
      keys = []
      for supplier_path in action_items['supplier_paths']:
        payload = supplier_path.get('request', {}).get('body', {})
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
  # for testing purposes
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
  api = ApiParser('api_parser_conf.yml')
  # print_action(api, 'complex_action', values)
  class_code = api.generate_class()
  print(class_code)


if __name__ == '__main__':
  main()
