import json
import json
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, List, Union

import requests

from src.domain.value_objects.api_response import ApiResponse
from src.domain.value_objects.obj_utils import Obj


class ApiIntegrator:
  def __init__(self, config_path: str):
    config_path = Path(__file__).resolve().parent.parent.parent / config_path
    self.config = Obj.from_yaml(config_path)
    self.vars = self.config.vars if self.config.has('vars') else Obj({})
    self.constants = self.config.constants if self.config.has('constants') else Obj({})
    self.session = requests.Session()
    self.latest_response = None
    self._setup_logging()
    self.i = 0

    # Initialize my_app_server
    self.vars['my_app_server'] = self.config.my_app_server if self.config.has(
      'my_app_server') else 'http://localhost:8000'

  def _setup_logging(self):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

  def perform_action(self, action_name: str, params: Obj = None):
    action = self.config.actions.get(action_name)
    if not action:
      raise ValueError(f"Action '{action_name}' not found in config")

    merged_params = Obj({**self.vars.to_dict(), **self.constants.to_dict(), **(params.to_dict() if params else {})})
    self.i += 1
    logging.info(f"[{self.i}] {action_name}: {merged_params}")
    for perform in action.performs:
      self.execute_perform(perform, merged_params)

  def execute_perform(self, perform_info: Obj, params: Obj):
    action = perform_info.perform
    data = action.data if isinstance(action, Obj) and action.has('data') else Obj({})
    logging.info(f"Perform: {action}")

    if isinstance(action, Obj):
      action_str = action.action
    elif isinstance(action, str):
      action_str = action
    else:
      raise ValueError(f"Invalid action type: {type(action)}")

    action_parts = action_str.split('.')
    if len(action_parts) > 1:
      handler_name = f'_handle_{action_parts[0]}'
      handler = getattr(self, handler_name, None)
      if handler:
        handler(action_str, data, params)
      else:
        raise ValueError(f"Unknown action: {action_str}")
    else:
      if action_str in self.config.actions:
        self.perform_action(action_str, params)
      else:
        handler_name = f'_handle_{action_str}'
        handler = getattr(self, handler_name, None)
        if handler:
          handler(data, params)
        else:
          raise ValueError(f"Unknown action: {action_str}")

    if 'responses' in perform_info:
      self._handle_responses(perform_info.responses, params)

  def _handle_http(self, command: str, data: Obj, params: Obj):
    method = command.split('.')[1].upper()
    endpoint = data.get('path', '') or data.get('url', '')
    url = self.render_template(endpoint, params)
    headers = Obj({k: self.render_template(v, params) for k, v in data.get('headers', Obj({})).items()})
    body_data = data.get('body', Obj({}))
    query = Obj({k: self.render_template(v, params) for k, v in data.get('query', Obj({})).items()})

    # Remove None values from query parameters
    query_dict = {k: v for k, v in query.to_dict().items() if v is not None}

    def log_and_request(body):
      """Helper function to log request and make HTTP call."""
      logging.info(f"Request: {method} {url} {headers} {query} {body}")
      response = self.session.request(method, url, headers=headers.to_dict(), data=body, params=query_dict)
      api_response = ApiResponse(response)
      params['response'] = api_response
      self.latest_response = api_response
      self.vars['response'] = api_response
      logging.info(f'Response [{response.status_code}] {response.text[:200]}')

    if data.get('type') == 'bulk':
      wrapper = data.get('wrapper', '')
      items = self.render_template(body_data, params)
      for item in items:
        wrapped_item = {wrapper: item} if wrapper else item
        body = json.dumps(wrapped_item)
        log_and_request(body)
    else:
      body = self.render_template(json.dumps(body_data.to_dict()), params)
      log_and_request(body)

  def _handle_log(self, command: str, data: Obj, params: Obj):
    level = command.split('.')[1]
    if not (isinstance(data, str)):
      data = data.to_dict()
    message = self.render_template(data, params)
    getattr(logging, level)(message)

  def _handle_action(self, command: str, data: Obj, params: Obj):
    action_name = command.split('.')[1]
    self.perform_action(action_name, params)

  def _handle_vars(self, command: str, data: Obj, params: Obj):
    operation = command.split('.')[1]
    if operation == 'set':
      for key, value in data.items():
        self.vars[key] = self.render_template(value, params)
    elif operation == 'get':
      for key in data:
        params[key] = self.vars.get(key)
    else:
      raise ValueError(f"Unknown vars operation: {operation}")

  def _handle_responses(self, responses: List[Obj], params: Obj):
    for response in responses:
      for condition_type in ['is_success', 'is_error']:
        if response.has(condition_type) and self._check_response_conditions(response[condition_type], params):
          for perform in response.get('performs', []):
            if isinstance(perform, Obj) and perform.has('perform'):
              self.execute_perform(perform, params)
            elif isinstance(perform, dict) and 'perform' in perform:
              self.execute_perform(Obj(perform), params)
            else:
              logging.warning(f"Invalid perform object: {perform}")

          return True  # Indicate that a response condition was met

    logging.warning("No matching response conditions found")

  def _check_response_conditions(self, conditions: Obj, params: Obj) -> bool:
    logging.info(f"conditions: {conditions}, params: {params}")
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

  def render_template(self, template: Union[str, Obj, List], params: Obj) -> Any:
    if isinstance(template, str):
      result = re.sub(r'\{\{(.+?)\}\}', lambda m: self.render_value(m.group(1).strip(), params), template)
      logging.debug(f"Rendered template: {template} -> {result}")
      return result
    elif isinstance(template, Obj):
      return Obj({k: self.render_template(v, params) for k, v in template.items()})
    elif isinstance(template, list):
      return [self.render_template(item, params) for item in template]
    return template

  def render_value(self, key: str, params: Obj) -> str:
    value = self.get_value(key, params)
    if isinstance(value, dict):
      return json.dumps(value)
    elif isinstance(value, ET.Element):
      return ET.tostring(value, encoding='unicode')
    return str(value)

  def get_value(self, key: str, params: Obj) -> Any:
    if key.startswith('response.'):
      response_key = key[9:]  # Remove 'response.' prefix
      if self.latest_response:
        if response_key in ['json', 'body']:
          return self.latest_response.body
        elif hasattr(self.latest_response, response_key):
          return getattr(self.latest_response, response_key)
        else:
          # Split the key to access nested attributes or array indices
          nested_keys = response_key.split('.')
          value = self.latest_response.json
          for sub_key in nested_keys:
            if isinstance(value, dict) and sub_key in value:
              value = value[sub_key]
            elif isinstance(value, list) and sub_key.isdigit():
              index = int(sub_key)
              if index < len(value):
                value = value[index]
              else:
                logging.warning(f"Array index out of range: {sub_key}")
                return f"{{{{ {key} }}}}"
            else:
              logging.warning(f"Unknown response attribute: {response_key}")
              return f"{{{{ {key} }}}}"
          return value
      else:
        logging.warning(f"No response available for key: {key}")
        return f"{{{{ {key} }}}}"

    if key == 'supplier_server.url':
      supplier_server = params.get('supplier_server') or self.vars.get('supplier_server') or self.constants.get(
        'supplier_server')
      if isinstance(supplier_server, Obj):
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
  config_relative_path = 'infrastructure/config/reqres_in.yml'
  integrator = ApiIntegrator(config_relative_path)

  # Example usage
  integrator.perform_action('test_crud')
  # integrator.perform_action('get_item_part', Obj({'id_item': '123', 'id_part': '456'}))


if __name__ == '__main__':
  main()
