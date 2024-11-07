from pathlib import Path
from typing import Union

from src.domain.value_objects.obj_utils import Obj


class OasToApiIntegratorSpecificationMapper:
  def __init__(self, full_path: str):
    self.api_spec = Obj.from_yaml(full_path)

  def oas_to_ais(self) -> Obj:
    """ Map the OpenAPI Specification to an API Integrator Specification (AIS). """
    servers = self._map_servers()
    default_server = next((server for server in servers if server['id'] == 'prod'),
                          servers[0] if servers else {'id': 'test', 'url': 'http://test.example.com'})

    return Obj({
      'api_integrator': '0.0.1',
      'info': self._map_info(),
      'supplier_servers': servers,
      'tags': self._map_tags(),
      'actions': self._map_actions(),
      'vars': {
        'supplier_server': default_server
      },
      'constants': {}
    })

  def _map_info(self) -> dict:
    info = self.api_spec.info
    return {
      'title': info.title,
      'version': info.version,
      'description': info.get('description', ''),
      'contact': info.get('contact', {}),
      'lang': 'python'
    }

  def _map_servers(self) -> list:
    servers = []
    for i, server in enumerate(self.api_spec.servers):
      url = server.url.lower()
      server_id = f'server_{i}' if any(env in url for env in ['sandbox', 'test', 'staging', 'dev']) else 'prod'

      servers.append({
        'id': server_id,
        'url': server.url,
        'description': server.get('description', '')
      })

    # Ensure 'prod' is always the first server if it exists
    servers.sort(key=lambda x: x['id'] != 'prod')
    return servers

  def _map_tags(self) -> list:
    return [
      {
        'name': tag.name,
        'description': tag.get('description', '')
      }
      for tag in self.api_spec.tags
    ]

  def _map_actions(self) -> dict:
    actions = {}
    for path, path_item in self.api_spec.paths.items():
      for method, content in path_item.items():
        if method not in ['get', 'post', 'put', 'delete', 'patch']:
          continue
        print(f"Processing operation: {method} {path}")
        action_name = content.summary.lower().replace(' ', '_') or f"{method}_{path.replace('/', '_')}"
        actions[action_name] = self._map_operation_to_action(path, method, content)
    return actions

  def _map_operation_to_action(self, path: str, method: str, operation: Obj) -> dict:
    return {
      'tags': operation.get('tags', []),
      'description': operation.get('description', ''),
      'performs': [
        {
          'perform': {
            'action': f"http.{method}",
            'data': {
              'path': f"{{{{supplier_server.url}}}}{path}",
              **({'headers': self._map_headers(operation)} if self._map_headers(operation) else {}),
              **({'query': self._map_query_params(operation)} if self._map_query_params(operation) else {}),
              **({'body': self._map_request_body(operation)} if self._map_request_body(operation) else {})
            }
          },
          'responses': self._map_responses(operation)
        }
      ]
    }

  def _map_headers(self, operation: Obj) -> Obj:
    headers = Obj({})
    if operation.has('parameters'):
      headers = Obj({
        param.name: f"{{{{{param.name}}}}}" if param.has('name') else '{{headers}}'
        for param in operation.parameters
        if param.get('in') == 'header'
      })
      # print(f"Mapped headers: {headers}")
    return headers

  def _map_query_params(self, operation: Obj) -> dict:
    query_params = {}
    if operation.has('parameters'):
      query_params = {
        param.name: f"{{{{{param.name}}}}}" if param.has('name') else '{{params}}'
        for param in operation.parameters
        if param.get('in') == 'query'
      }
      # print(f"Mapped query parameters: {query_params}")
    return query_params

  def _map_request_body(self, operation: Obj) -> dict:
    request_body = operation.get('requestBody', {})
    if not request_body:
      return {}

    content = request_body.get('content', {})
    json_content = content.get('application/json', {})
    schema = json_content.get('schema', {})

    return self._map_schema_to_template(schema)

  def _map_schema_to_template(self, schema: Obj) -> dict:
    if schema.get('type') == 'object':
      return {
        prop: f"{{{{{prop}}}}}"
        for prop in schema.get('properties', {}).keys()
      }
    return {}

  def _map_responses(self, operation: Obj) -> list:
    responses = []
    for status_code, response_data in operation.get('responses', {}).items():
      responses.append(self._map_single_response(status_code, response_data))
    return responses

  def _map_single_response(self, status_code: str, response_data: Obj) -> dict:
    response = {
      'is_success' if str(status_code).startswith('2') else 'is_error': {
        'code': int(status_code)
      },
      'performs': [
        self._create_log_perform(status_code)
      ]
    }
    vars_set_perform = self._create_vars_set_perform(response_data)
    if vars_set_perform is not None:
      response['performs'].append(vars_set_perform)
    return response

  def _create_log_perform(self, status_code: str) -> dict:
    return {
      'perform': {
        'action': 'log.info' if str(status_code).startswith('2') else 'log.error',
        'data': f"Response: {{{{response.body}}}}"
      }
    }

  def _create_vars_set_perform(self, response_data: Obj) -> dict:
    vars_set_data = {}

    if response_data.has('content') and response_data.content.has('application/json'):
      json_content = response_data.content['application/json']
      # Check if there's an example in the content
      if json_content.has('example'):
        example_data = json_content.example
        self._extract_placeholders(example_data, '', 'response.body', vars_set_data)
    if vars_set_data:
      return {
        'perform': {
          'action': 'vars.set',
          'data': vars_set_data
        }
      }

  def _extract_placeholders(self, data, parent_key, assigned_key, vars_set_data):
    """
    Recursively extracts placeholders for nested JSON structures.
    """
    if isinstance(data, Obj) or isinstance(data, dict):
      for key, value in data.items():
        full_key = f"{parent_key}_{key}" if parent_key else key
        new_assigned_key = f"{assigned_key}.{key}" if assigned_key else key
        self._extract_placeholders(value, full_key, new_assigned_key, vars_set_data)
    elif isinstance(data, list):
      for i, item in enumerate(data):
        list_key = f"{parent_key}_{i}" if parent_key else ''
        new_assigned_key = f"{assigned_key}[{i}]"
        self._extract_placeholders(item, list_key, new_assigned_key, vars_set_data)
    else:
      vars_set_data[parent_key] = f"{{{{{assigned_key}}}}}"

  def _create_sample_response_performs(self, schema: Obj, content_type: str) -> list:
    performs = []
    # Log the sample response
    performs.append({
      'perform': {
        'action': 'log.info',
        'data': f'Sample {content_type} response received'
      }
    })

    # Create a perform action to send the sample response to my_app_server
    sample_response_body = self._create_sample_response_body(schema, content_type)
    if sample_response_body:
      performs.append({
        'perform': {
          'action': 'http.post',
          'type': 'bulk',
          'wrapper': 'item',
          'data': {
            'url': '{{my_app_server.url}}/items',
            'headers': {
            },
            'body': sample_response_body
          }
        }
      })

    return performs

  def _create_sample_response_body(self, schema: Obj, content_type: str) -> Union[dict, str]:
    if content_type == 'json':
      return self._create_json_response_body(schema)
    elif content_type == 'xml':
      return self._create_xml_response_body(schema)
    else:
      return {}

  def _create_json_response_body(self, schema: Obj) -> dict:
    if schema.get('type') == 'object':
      return {prop: f'{{{{response.json.{prop}}}}}' for prop in schema.get('properties', {}).keys()}
    elif schema.get('type') == 'array':
      items_schema = schema.get('items', {})
      if items_schema.get('type') == 'object':
        return [{prop: f'{{{{response.json[].{prop}}}}}' for prop in items_schema.get('properties', {}).keys()}]
    return {}

  def _create_xml_response_body(self, schema: Obj) -> dict:
    if schema.get('type') == 'object':
      return {prop: f'{{{{response.xml.{prop}}}}}' for prop in schema.get('properties', {}).keys()}
    elif schema.get('type') == 'array':
      items_schema = schema.get('items', {})
      if items_schema.get('type') == 'object':
        return [{prop: f'{{{{response.xml[].{prop}}}}}' for prop in items_schema.get('properties', {}).keys()}]
    return {}


def main():
  # Paths (input relative to infrastructure directory)
  parent_path = Path(__file__).parent.parent.parent
  input_path = parent_path / 'infrastructure/specs/oas/cva.yml'
  output_path = parent_path / 'infrastructure/specs/api_integrator' / (Path(input_path).stem + '_ai.yaml')

  # Conversion process
  mapper = OasToApiIntegratorSpecificationMapper(input_path)
  ais = mapper.oas_to_ais()
  ais.save(str(output_path))
  print(f"API Integrator configuration has been saved to {output_path}")


if __name__ == '__main__':
  main()
