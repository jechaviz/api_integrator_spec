from src.infrastructure.services.oas_parser.abstract_oas_parser import AbstractOasParser
from src.domain.entities.api_specification import ApiSpecification

class Oas31Parser(AbstractOasParser):
    def parse(self, oas_file_path: str = '') -> ApiSpecification:
        if oas_file_path:
            self.load_data(oas_file_path)

        api_specification = ApiSpecification(
            self.get_api_name(),
            self.get_base_url(),
            self.get_version(),
            self.parse_servers(self.data.get('servers', [])),
            self.data.get('info', {})
        )

        self.parse_paths(api_specification)
        self.parse_components(api_specification)
        self.parse_webhooks(api_specification)
        api_specification.set_external_docs(self.data.get('externalDocs', {}))
        api_specification.set_tags(self.data.get('tags', []))

        return api_specification

    def parse_servers(self, servers: list) -> list:
        return [
            {
                'url': server['url'],
                'description': server.get('description'),
                'variables': server.get('variables', {})
            }
            for server in servers
        ]

    def parse_paths(self, api_specification: ApiSpecification) -> None:
        paths = self.data.get('paths', {})
        for path, methods in paths.items():
            for method, operation in methods.items():
                responses = self.parse_responses(operation.get('responses', {}))
                api_specification.add_endpoint({
                    'path': path,
                    'method': method.upper(),
                    'operationId': operation.get('operationId', self.generate_operation_id(method, path)),
                    'summary': operation.get('summary'),
                    'description': operation.get('description'),
                    'parameters': operation.get('parameters', []),
                    'requestBody': operation.get('requestBody'),
                    'responses': responses,
                    'tags': operation.get('tags', []),
                    'security': operation.get('security', []),
                })

    def parse_responses(self, responses: dict) -> dict:
        parsed_responses = {}
        for status_code, response in responses.items():
            parsed_responses[status_code] = {
                'description': response.get('description', ''),
                'headers': response.get('headers', {}),
                'content': self.parse_response_content(response.get('content', {})),
            }
        return parsed_responses

    def parse_response_content(self, content: dict) -> dict:
        parsed_content = {}
        for media_type, media_type_object in content.items():
            parsed_content[media_type] = {
                'schema': media_type_object.get('schema'),
                'examples': media_type_object.get('examples'),
            }
        return parsed_content

    def parse_components(self, api_specification: ApiSpecification) -> None:
        components = self.data.get('components', {})
        component_types = {
            'schemas': 'set_schemas',
            'responses': 'set_responses',
            'parameters': 'set_parameters',
            'examples': 'set_examples',
            'requestBodies': 'set_request_bodies',
            'headers': 'set_headers',
            'securitySchemes': 'set_security_schemes',
            'links': 'set_links',
            'callbacks': 'set_callbacks',
            'pathItems': 'set_path_items'
        }

        for component_type, setter in component_types.items():
            if component_type in components:
                getattr(api_specification, setter)(components[component_type])

        self.parse_security_requirements(api_specification)

    def parse_security_requirements(self, api_specification: ApiSpecification) -> None:
        if 'security' in self.data:
            api_specification.set_security_requirements(self.data['security'])

    def parse_webhooks(self, api_specification: ApiSpecification) -> None:
        if 'webhooks' in self.data:
            api_specification.set_webhooks(self.data['webhooks'])

    def get_api_name(self) -> str:
        return self.data.get('info', {}).get('title', 'Unnamed API')

    def get_base_url(self) -> str:
        servers = self.data.get('servers', [])
        return servers[0]['url'] if servers else ''

    def get_version(self) -> str:
        return self.data.get('info', {}).get('version', '1.0.0')
