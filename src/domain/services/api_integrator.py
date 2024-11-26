import json
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, List, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

import requests
import aiohttp
import asyncio
from flask import Flask, jsonify
from snoop import snoop
import pykwalify.core

from src.domain.value_objects.api_response import ApiResponse
from src.domain.value_objects.obj_utils import Obj


class ApiIntegrator:
  def __init__(self, config_path: str, max_workers: int = 10, schema_path: str = None):
    config_path = Path(__file__).resolve().parent.parent.parent / config_path

    # Default schema path if not provided
    # if schema_path is None:
    #  schema_path = Path(__file__).resolve().parent.parent.parent / 'infrastructure' / 'schemas' / 'api_integrator_schema.yml'

    # Validate configuration against schema
    # try:
    #  pykwalify.core.Core(source_file=str(config_path), schema_files=[str(schema_path)]).validate()
    # except Exception as e:
    #  logging.error(f'Configuration validation failed: {e}')
    #  raise ValueError(f'Invalid configuration: {e}')

    self.config = Obj.from_yaml(config_path)
    self.vars = self.config.vars if self.config.has('vars') else Obj({})
    self.constants = self.config.constants if self.config.has('constants') else Obj({})
    self.session = requests.Session()
    self.latest_response = None
    self._setup_logging()
    self.action_number = 0
    self.action_depth = 0  # Track recursion depth
    self.app = None
    self.max_workers = max_workers
    self.config_path = config_path  # Save config path for updates

    # Check if we should run as server
    if self.config.get('as_server', False):
      self.app = Flask(__name__)
      self._setup_endpoints()

    # Initialize my_app_server
    self.vars['my_app_server'] = self.config.my_app_server if self.config.has(
      'my_app_server') else 'http://localhost:8000'

  def _setup_logging(self):
    if not self.config.get('as_server', False):
      logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                          datefmt='%Y-%m-%d %H:%M:%S')

  def _setup_endpoints(self):
    '''Setup Flask endpoints for each action in the config'''
    logging.info(' Registered endpoints:')
    for action_name, action_config in self.config.actions.items():
      endpoint = f'/{action_name}'
      methods = self._get_action_methods(action_config)

      self.app.add_url_rule(
        endpoint,
        endpoint[1:],  # Route name
        lambda a=action_name: self._handle_endpoint(a),
        methods=methods
      )
      logging.info(f" {endpoint} [{', '.join(methods)}]")

  def _get_action_methods(self, action_config: Obj) -> List[str]:
    '''Extract HTTP methods from action configuration'''
    methods = set()

    # Look through all performs to find HTTP methods
    for perform in action_config.performs:
      if isinstance(perform.perform, Obj) and perform.perform.action.startswith('http.'):
        method = perform.perform.action.split('.')[1].upper()
        methods.add(method)

    # If no HTTP methods found, default to GET
    return list(methods) if methods else ['GET']

  def _handle_endpoint(self, action_name: str):
    '''Handle web requests to action endpoints'''
    try:
      self.perform_action(action_name)
      response_data = {
        'status': 'success',
        'action': action_name,
        'response': self.latest_response.body if self.latest_response else None
      }
      return jsonify(response_data)
    except Exception as e:
      return jsonify({
        'status': 'error',
        'action': action_name,
        'error': str(e)
      }), 500

  def perform_action(self, action_name: str, params: Obj = None):
    action = self.config.actions.get(action_name)
    if not action:
      raise ValueError(f"Action '{action_name}' not found in config")
    merged_params = Obj({**(params.to_dict() if params else {}), **self.vars.to_dict(), **self.constants.to_dict()})

    # Increment depth counter
    self.action_depth += 1
    self.action_number += 1

    # logging.info(f'[{self.i}] {action_name} {merged_params}')
    logging.info(f'[{self.action_number}] {action_name}')

    try:
      for perform in action.performs:
        self.execute_perform(perform, merged_params)
    finally:
      # Decrement depth counter
      self.action_depth -= 1
      # Reset step counter only when exiting top level action
      if self.action_depth == 0:
        self.action_number = 0

  def execute_perform(self, perform_info: Obj, params: Obj):
    action = perform_info.perform
    data = action.data if isinstance(action, Obj) and action.has('data') else Obj({})
    # logging.info(f'Perform: {action}')

    if isinstance(action, Obj):
      action_str = action.action
    elif isinstance(action, str):
      action_str = action
    else:
      raise ValueError(f'Invalid action type: {type(action)}')

    action_parts = action_str.split('.')
    if len(action_parts) > 1:
      handler_name = f'_handle_{action_parts[0]}'
      handler = getattr(self, handler_name, None)
      if handler:
        handler(action_str, data, params)
      else:
        raise ValueError(f'Unknown action: {action_str}')
    else:
      if action_str in self.config.actions:
        self.perform_action(action_str, params)
      else:
        handler_name = f'_handle_{action_str}'
        handler = getattr(self, handler_name, None)
        if handler:
          handler(data, params)
        else:
          raise ValueError(f'Unknown action: {action_str}')

    if 'responses' in perform_info:
      self._handle_responses(perform_info.responses, params)

  async def _async_http_request(self, method: str, url: str, headers: dict = None,
                                data: str = None, params: dict = None) -> ApiResponse:
    '''Async HTTP request method using aiohttp'''
    async with aiohttp.ClientSession() as session:
      logging.info(f'Async Request: 🔹{method}🔹 {url} {headers} {params} {data}')
      async with session.request(method, url, headers=headers, data=data, params=params) as response:
        body = await response.text()
        response_obj = requests.Response()
        response_obj.status_code = response.status
        response_obj.url = str(response.url)
        response_obj.headers = dict(response.headers)
        response_obj._content = body.encode('utf-8')
        api_response = ApiResponse(response_obj)
        logging.info(f'Async Response [{response.status}] {body[:200]}')
        return api_response

  def _threaded_bulk_request(self, method: str, url: str, items: List[Any],
                             headers: dict = None, wrapper: str = '') -> List[ApiResponse]:
    '''Perform bulk requests using ThreadPoolExecutor'''

    def single_request(item):
      wrapped_item = {wrapper: item} if wrapper else item
      body = json.dumps(wrapped_item)
      headers_copy = headers.copy() if headers else {}
      headers_copy['Content-Type'] = 'application/json'

      response = self.session.request(method, url, headers=headers_copy, data=body)
      return ApiResponse(response)

    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
      futures = [executor.submit(single_request, item) for item in items]
      return [future.result() for future in as_completed(futures)]

  async def _async_bulk_request(self, method: str, url: str, items: List[Any],
                                headers: dict = None, wrapper: str = '') -> tuple[Any]:
    '''Async bulk request method'''

    async def single_request(item):
      wrapped_item = {wrapper: item} if wrapper else item
      body = json.dumps(wrapped_item)
      headers_copy = headers.copy() if headers else {}
      headers_copy['Content-Type'] = 'application/json'

      async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers_copy, data=body) as response:
          body_text = await response.text()
          response_obj = requests.Response()
          response_obj.status_code = response.status
          response_obj.url = str(response.url)
          response_obj.headers = dict(response.headers)
          response_obj._content = body_text.encode('utf-8')
          return ApiResponse(response_obj)

    tasks = [single_request(item) for item in items]
    return await asyncio.gather(*tasks)

  def _update_config_with_response(self, action_name: str, response: ApiResponse):
    """Update configuration file with the error response."""
    if self.config.get('enhance_conf_with_responses', False):
      logging.info(f'Updating config with error response for {action_name}')
      if not self.config.actions[action_name].has('sample_responses'):
        self.config.actions[action_name].sample_responses = Obj([])

      # Add the new error response to the sample_responses list
      self.config.actions[action_name].sample_responses.append({
        'status_code': response.status_code,
        'body': response.body[:200]  # Limit body to 200 chars for readability
      })
      self.config.save(self.config_path)

  def _handle_http(self, command: str, data: Obj, params: Obj):
    method = command.split('.')[1].upper()
    url = self._prepare_url(data, params)
    headers_dict = self._prepare_headers(data, params)
    query_dict = self._prepare_query(data, params)
    body_data = data.get('body', Obj({}))

    if data.get('type') == 'bulk':
      self._handle_bulk_request(method, url, body_data, headers_dict, data, params)
    else:
      self._handle_single_request(method, url, body_data, headers_dict, query_dict, data, params)

  def _prepare_url(self, data: Obj, params: Obj) -> str:
    endpoint = data.get('path', '') or data.get('url', '')
    return self.render_template(endpoint, params)

  def _prepare_headers(self, data: Obj, params: Obj) -> dict:
    headers = Obj({k: self.render_template(v, params) for k, v in data.get('headers', Obj({})).items()})
    return headers.to_dict()

  def _prepare_query(self, data: Obj, params: Obj) -> dict:
    query = Obj({k: self.render_template(v, params) for k, v in data.get('query', Obj({})).items()})
    return {k: v for k, v in query.to_dict().items() if v is not None}

  def _handle_bulk_request(self, method: str, url: str, body_data: Obj, headers_dict: dict, data: Obj, params: Obj):
    wrapper = data.get('wrapper', '')
    items = self.render_template(body_data, params)

    # Prefer async if available, fallback to threading
    responses = self._execute_bulk_request(method, url, items, headers_dict, wrapper, data.get('async', False))

    # Store responses in vars for further processing
    self.vars['bulk_responses'] = responses
    self.latest_response = responses[-1] if responses else None

    # Perform individual request logging and processing
    for item in items:
      wrapped_item = {wrapper: item} if wrapper else item
      body = json.dumps(wrapped_item)
      self._log_and_process_request(method, url, headers_dict, body, params)

  def _handle_single_request(self, method: str, url: str, body_data: Obj, headers_dict: dict, query_dict: dict,
                             data: Obj, params: Obj):
    body = self.render_template(json.dumps(body_data.to_dict()), params)

    # Check for async request
    response = self._execute_single_request(method, url, headers_dict, body, query_dict, data.get('async', False))

    params['response'] = response
    self.latest_response = response
    self.vars['response'] = response

    # Log and process the request
    self._log_and_process_request(method, url, headers_dict, body, params, query_dict)

  def _execute_bulk_request(self, method: str, url: str, items: List, headers_dict: dict, wrapper: str,
                            is_async: bool) -> List[ApiResponse]:
    try:
      if is_async:
        return asyncio.run(self._async_bulk_request(method, url, items, headers_dict, wrapper))
    except Exception as e:
      logging.error(f'Async bulk request failed: {e}')

    return self._threaded_bulk_request(method, url, items, headers_dict, wrapper)

  def _execute_single_request(self, method: str, url: str, headers_dict: dict, body: str, query_dict: dict,
                              is_async: bool) -> ApiResponse:
    try:
      if is_async:
        return asyncio.run(self._async_http_request(method, url, headers_dict, body, query_dict))
    except Exception as e:
      logging.error(f'Async request failed: {e}')

    response = self.session.request(method, url, headers=headers_dict, data=body, params=query_dict)
    return ApiResponse(response)

  def _log_and_process_request(self, method: str, url: str, headers: dict, body: str, params: Obj,
                               query_dict: dict = None):
    query_dict = query_dict or {}
    logging.info(f'Request: 🔹{method}🔹 {url} {headers} {query_dict} {body}')
    response = self.session.request(method, url, headers=headers, data=body, params=query_dict)
    api_response = ApiResponse(response)
    params['response'] = api_response
    self.latest_response = api_response
    self.vars['response'] = api_response
    logging.info(f'Response [{response.status_code}] {response.text[:200]}')

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
        # Always render the value - render_template handles all types
        rendered_value = self.render_template(value, params)
        # Only update and log if the value actually changed
        if rendered_value != value:
          self.vars[key] = rendered_value
          logging.info(f'Updated var {key}={rendered_value}')
    elif operation == 'get':
      for key in data:
        params[key] = self.vars.get(key)
    else:
      raise ValueError(f'Unknown vars operation: {operation}')

  def _handle_responses(self, responses: List[Obj], params: Obj):
    '''Handle response conditions and execute corresponding performs.'''
    for response in responses:
      # Check both success and error conditions
      for condition_type in ['is_success', 'is_error']:
        if not response.has(condition_type):
          continue

        if self._check_response_conditions(response[condition_type]):
          self._execute_response_performs(response.get('performs', []), params)
          return True

    logging.warning('No matching response conditions found')
    return False

  def _execute_response_performs(self, performs: List[Union[Obj, dict]], params: Obj):
    '''Execute a list of perform actions for a matching response.'''
    for perform in performs:
      if isinstance(perform, (Obj, dict)):
        # Convert dict to Obj if needed
        perform_obj = perform if isinstance(perform, Obj) else Obj(perform)
        if perform_obj.has('perform'):
          self.execute_perform(perform_obj, params)
        else:
          logging.warning(f'Missing perform key in object: {perform}')
      else:
        logging.warning(f'Invalid perform object type: {type(perform)}')

  def _check_response_conditions(self, conditions: Obj) -> bool:
    response = self.latest_response
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

  def _get_response_value(self, key: str) -> Any:
    '''Get a value from the latest response using dot notation.'''
    if not self.latest_response:
      logging.warning(f'No response available for key: {key}')
      return f'{{{{ {key} }}}}'

    response_key = key[9:]  # Remove 'response.' prefix

    # Handle direct response attributes first
    if hasattr(self.latest_response, response_key):
      return getattr(self.latest_response, response_key)

    # For body/json access, try to parse JSON first
    try:
      json_data = self._parse_response_json()
      if not json_data:
        return None

      # Return full JSON for body/json keys
      if response_key in ['json', 'body']:
        return json_data

      # Navigate nested structure
      return self._get_nested_value(json_data, response_key)

    except Exception as e:
      logging.warning(f'Error accessing response value: {e}')
      return None

  def _parse_response_json(self) -> Union[dict, list, None]:
    '''Parse the response body as JSON.'''
    try:
      return json.loads(self.latest_response.body)
    except json.JSONDecodeError:
      logging.warning('Response body is not valid JSON')
      return None

  def _get_nested_value(self, data: Union[dict, list], key_path: str) -> Any:
    '''Get a nested value using dot notation.'''
    # Remove 'body' from path if present
    nested_keys = [k for k in key_path.split('.') if k != 'body']

    value = data
    for key in nested_keys:
      if isinstance(value, dict):
        if key in value:
          value = value[key]
        else:
          logging.warning(f'Key {key} not found in response')
          return None
      elif isinstance(value, list) and key.isdigit():
        index = int(key)
        if 0 <= index < len(value):
          value = value[index]
        else:
          logging.warning(f'Array index {key} out of range')
          return None
      else:
        logging.warning(f'Cannot access {key} in {type(value)}')
        return None
    return value

  def _get_supplier_server_url(self, params: Obj) -> str:
    supplier_server = (
        params.get('supplier_server') or
        self.vars.get('supplier_server') or
        self.constants.get('supplier_server')
    )

    if isinstance(supplier_server, Obj):
      if supplier_server.has('url'):
        return supplier_server.url
      server_id = supplier_server.get('id')
      if server_id:
        return next((server.url for server in self.config.supplier_servers if server.id == server_id),
                    f'{{{{ supplier_server.url }}}}')
    elif isinstance(supplier_server, str):
      return next((server.url for server in self.config.supplier_servers if server.id == supplier_server),
                  f'{{{{ supplier_server.url }}}}')

    logging.warning(f'Could not find supplier_server.url for {supplier_server}')
    return f'{{{{ supplier_server.url }}}}'

  def render_template(self, template: Union[str, Obj, List], params: Obj) -> Any:
    if isinstance(template, str):
      # First render any template variables
      result = re.sub(r'\{\{(.+?)\}\}', lambda m: self.render_value(m.group(1).strip(), params), template)
      logging.debug(f'Rendered template: {template} -> {result}')
      return result
    elif isinstance(template, Obj):
      return Obj({k: self.render_template(v, params) for k, v in template.items()})
    elif isinstance(template, list):
      return [self.render_template(item, params) for item in template]
    return template

  def render_value(self, key: str, params: Obj) -> str:
    # First check if it's a response path
    if key.startswith('response.'):
      response_value = self._get_response_value(key)
      if response_value is not None:
        return str(response_value)

    # Then try normal value lookup
    value = self.get_value(key, params)
    if value == f'{{{{ {key} }}}}':  # If not found in params/vars/constants
      # Try getting from vars directly for log messages
      if key in self.vars:
        return str(self.vars[key])

    # Format the value appropriately
    if isinstance(value, dict):
      return json.dumps(value)
    elif isinstance(value, ET.Element):
      return ET.tostring(value, encoding='unicode')
    return str(value)

  def get_value(self, key: str, params: Obj) -> Any:
    # Handle special cases first
    if key.startswith('response.'):
      return self._get_response_value(key)
    elif key == 'supplier_server.url':
      return self._get_supplier_server_url(params)

    value = (
        params.get(key) or
        self.vars.get(key) or
        self.constants.get(key) or
        f'{{{{ {key} }}}}'
    )
    logging.debug(f"Getting value for key '{key}': {value}")
    return value


def main():
  config_relative_path = 'infrastructure/specs/api_integrator/cva_ai.yaml'
  integrator = ApiIntegrator(config_relative_path)
  for action_name, action_body in integrator.config.actions.items():
    for perform in action_body.performs:
      if perform.perform.action == 'http.get':
        integrator.perform_action(action_name)


if __name__ == '__main__':
  main()