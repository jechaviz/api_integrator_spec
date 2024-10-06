import yaml
import os
from pathlib import Path

from snoop import snoop

from src.domain.value_objects.yml_obj import YmlObj

class OasToApiIntegratorMapper:
    def __init__(self, oas_file_path: str):
        base_path = Path(__file__).parent.parent / 'oas_specs'
        full_path = base_path / oas_file_path
        self.api_spec = self._load_oas(str(full_path))

    def _load_oas(self, file_path: str) -> YmlObj:
        with open(file_path, 'r') as f:
            return YmlObj(yaml.safe_load(f))

    def map_to_api_integrator_config(self) -> YmlObj:
        servers = self._map_servers()
        default_server = next((server for server in servers if server['id'] == 'prod'), servers[0] if servers else {'id': 'test', 'url': 'http://test.example.com'})
        
        return YmlObj({
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

    def _map_operation_to_action(self, path: str, method: str, operation: YmlObj) -> dict:
        return {
            'tags': operation.get('tags', []),
            'description': operation.get('description', ''),
            'performs': [
                {
                    'perform': {
                        'a': f"http.{method}",
                        'data': {
                            'path': f"{{{{supplier_server.url}}}}{path}",
                            'headers': self._map_headers(operation),
                            'query': self._map_query_params(operation),
                            'body': self._map_request_body(operation)
                        }
                    },
                    'responses': self._map_responses(operation)
                }
            ]
        }

    def _map_headers(self, operation: YmlObj) -> dict:
        return {
            param.name: f"{{{{headers.{param.name}}}}}"
            for param in operation.get('parameters', [])
            if param.get('in') == 'header'
        }

    def _map_query_params(self, operation: YmlObj) -> dict:
        return {
            param.name: f"{{{{params.{param.name}}}}}"
            for param in operation.get('parameters', [])
            if param.get('in') == 'query'
        }

    def _map_request_body(self, operation: YmlObj) -> dict:
        request_body = operation.get('requestBody', {})
        if not request_body:
            return {}
        
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        schema = json_content.get('schema', {})
        
        return self._map_schema_to_template(schema)

    def _map_schema_to_template(self, schema: YmlObj) -> dict:
        if schema.get('type') == 'object':
            return {
                prop: f"{{{{body.{prop}}}}}"
                for prop in schema.get('properties', {}).keys()
            }
        return {}

    def _map_responses(self, operation: YmlObj) -> list:
        responses = []
        for status_code, response_data in operation.get('responses', {}).items():
            responses.append(self._map_single_response(status_code, response_data))
        return responses

    def _map_single_response(self, status_code: str, response_data: YmlObj) -> dict:
        return {
            'is_success' if str(status_code).startswith('2') else 'is_error': {
                'code': int(status_code)
            },
            'performs': [
                self._create_log_perform(status_code),
                self._create_vars_set_perform()
            ]
        }

    def _create_log_perform(self, status_code: str) -> dict:
        return {
            'perform': {
                'a': 'log.info' if str(status_code).startswith('2') else 'log.error',
                'data': f"Response: {{{{response.body}}}}"
            }
        }

    def _create_vars_set_perform(self) -> dict:
        return {
            'perform': {
                'a': 'vars.set',
                'data': {
                    'last_response': '{{response.body}}'
                }
            }
        }


def main():
    # Define the input file path (relative to oas_specs directory)
    input_file = 'cva/cva.yml'

    # Create the mapper and generate the configuration
    mapper = OasToApiIntegratorMapper(input_file)
    config = mapper.map_to_api_integrator_config()

    # Generate the output file name
    output_file = Path(__file__).parent / 'infrastructure/config' / (Path(input_file).stem + '_ai.yaml')

    # Ensure the output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save the configuration to the output file
    with open(output_file, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)

    print(f"API Integrator configuration has been saved to {output_file}")


if __name__ == '__main__':
    main()