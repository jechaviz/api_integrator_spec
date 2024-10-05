from typing import Dict, Any, List
from src.domain.entities.api_specification import ApiSpecification
from src.domain.value_objects.yml_obj import YmlObj
from src.infrastructure.services.oas_parser.oas_parser_factory import OasParserFactory

class OasToApiIntegratorMapper:
    def __init__(self, oas_file_path: str):
        self.oas_parser = OasParserFactory.create(oas_file_path)
        self.api_spec = self.oas_parser.parse(oas_file_path)

    def map_to_api_integrator_config(self) -> Dict[str, Any]:
        config = {
            'api_integrator': '0.0.1',
            'info': self._map_info(),
            'supplier_servers': self._map_servers(),
            'tags': self._map_tags(),
            'actions': self._map_actions(),
            'vars': {},
            'constants': {}
        }
        return config

    def _map_info(self) -> Dict[str, Any]:
        info = self.api_spec.info
        return {
            'title': info.get('title', 'Unnamed API'),
            'version': info.get('version', '1.0.0'),
            'description': info.get('description', ''),
            'contact': info.get('contact', {}),
            'lang': 'python'  # Assuming Python as the default language
        }

    def _map_servers(self) -> List[Dict[str, Any]]:
        return [
            {
                'id': f'server_{i}',
                'url': server.get('url', ''),
                'description': server.get('description', '')
            }
            for i, server in enumerate(self.api_spec.servers)
        ]

    def _map_tags(self) -> List[Dict[str, str]]:
        return [
            {
                'name': tag.get('name', ''),
                'description': tag.get('description', '')
            }
            for tag in self.api_spec.tags
        ]

    def _map_actions(self) -> Dict[str, Any]:
        actions = {}
        for endpoint in self.api_spec.get_endpoints():
            action_name = endpoint['operationId'] or f"{endpoint['method'].lower()}_{endpoint['path'].replace('/', '_')}"
            actions[action_name] = self._map_endpoint_to_action(endpoint)
        return actions

    def _map_endpoint_to_action(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        action = {
            'tags': endpoint.get('tags', []),
            'description': endpoint.get('description', ''),
            'performs': [
                {
                    'perform': {
                        'a': f"http.{endpoint['method'].lower()}",
                        'data': {
                            'path': f"{{{{supplier_server.url}}}}{endpoint['path']}",
                            'headers': self._map_headers(endpoint),
                            'query': self._map_query_params(endpoint),
                            'body': self._map_request_body(endpoint)
                        }
                    },
                    'responses': self._map_responses(endpoint)
                }
            ]
        }
        return action

    def _map_headers(self, endpoint: Dict[str, Any]) -> Dict[str, str]:
        headers = {}
        for param in endpoint.get('parameters', []):
            if param.get('in') == 'header':
                headers[param['name']] = f"{{{{headers.{param['name']}}}}}"
        return headers

    def _map_query_params(self, endpoint: Dict[str, Any]) -> Dict[str, str]:
        query_params = {}
        for param in endpoint.get('parameters', []):
            if param.get('in') == 'query':
                query_params[param['name']] = f"{{{{params.{param['name']}}}}}"
        return query_params

    def _map_request_body(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        request_body = endpoint.get('requestBody', {})
        if not request_body:
            return {}
        
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        schema = json_content.get('schema', {})
        
        return self._map_schema_to_template(schema)

    def _map_schema_to_template(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        if schema.get('type') == 'object':
            properties = schema.get('properties', {})
            return {
                prop: f"{{{{body.{prop}}}}}"
                for prop in properties.keys()
            }
        return {}

    def _map_responses(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        responses = []
        for status_code, response_data in endpoint.get('responses', {}).items():
            response = {
                'is_success' if status_code.startswith('2') else 'is_error': {
                    'code': int(status_code)
                },
                'performs': [
                    {
                        'perform': {
                            'a': 'log.info' if status_code.startswith('2') else 'log.error',
                            'data': f"Response for {endpoint['method']} {endpoint['path']}: {{{{response.body}}}}"
                        }
                    },
                    {
                        'perform': {
                            'a': 'vars.set',
                            'data': {
                                f"last_{endpoint['method'].lower()}_response": '{{response.body}}'
                            }
                        }
                    }
                ]
            }
            responses.append(response)
        return responses

def map_oas_to_api_integrator(oas_file_path: str) -> Dict[str, Any]:
    mapper = OasToApiIntegratorMapper(oas_file_path)
    return mapper.map_to_api_integrator_config()
