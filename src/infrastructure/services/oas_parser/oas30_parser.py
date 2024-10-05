from src.infrastructure.services.oas_parser.abstract_oas_parser import AbstractOasParser
from src.domain.entities.api_specification import ApiSpecification

class Oas30Parser(AbstractOasParser):
    def parse(self, oas_file_path: str = '') -> ApiSpecification:
        if oas_file_path:
            self.load_data(oas_file_path)

        api_specification = self.create_api_specification()

        self.parse_paths(api_specification)
        self.parse_components(api_specification)
        self.parse_tags(api_specification)
        self.parse_external_docs(api_specification)

        return api_specification

    def create_api_specification(self) -> ApiSpecification:
        name = self.get_api_name()
        base_url = self.get_base_url()
        version = self.get_version()

        return ApiSpecification(name, base_url, version, self.data.get('servers', []), self.data.get('info', {}))

    def parse_paths(self, api_specification: ApiSpecification) -> None:
        paths = self.data.get('paths', {})
        for path, path_data in paths.items():
            for method, endpoint_data in path_data.items():
                endpoint = self.create_endpoint(path, method, endpoint_data)
                api_specification.add_endpoint(endpoint)

    def create_endpoint(self, path: str, method: str, endpoint_data: dict) -> dict:
        endpoint = {
            'path': path,
            'method': method.upper(),
            'operationId': endpoint_data.get('operationId', self.generate_operation_id(method, path)),
            'summary': endpoint_data.get('summary'),
            'description': endpoint_data.get('description'),
            'parameters': endpoint_data.get('parameters', []),
            'responses': endpoint_data.get('responses', {}),
            'requestBody': endpoint_data.get('requestBody'),
            'security': endpoint_data.get('security', []),
            'tags': endpoint_data.get('tags', []),
        }

        self.extract_response_examples(endpoint)
        return endpoint

    def extract_response_examples(self, endpoint: dict) -> None:
        for status_code, response_data in endpoint['responses'].items():
            content = response_data.get('content', {})
            json_content = content.get('application/json', {})
            examples = json_content.get('examples')
            if examples:
                endpoint['responses'][status_code]['examples'] = examples

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
            'callbacks': 'set_callbacks'
        }

        for component_type, setter in component_types.items():
            if component_type in components:
                getattr(api_specification, setter)(components[component_type])

        self.parse_security_requirements(api_specification)
        self.parse_servers(api_specification)

    def parse_security_requirements(self, api_specification: ApiSpecification) -> None:
        if 'security' in self.data:
            api_specification.set_security_requirements(self.data['security'])

    def parse_servers(self, api_specification: ApiSpecification) -> None:
        if 'servers' in self.data:
            api_specification.set_servers(self.data['servers'])

    def parse_tags(self, api_specification: ApiSpecification) -> None:
        if 'tags' in self.data:
            api_specification.set_tags(self.data['tags'])

    def parse_external_docs(self, api_specification: ApiSpecification) -> None:
        if 'externalDocs' in self.data:
            api_specification.set_external_docs(self.data['externalDocs'])

    def get_api_name(self) -> str:
        return self.data.get('info', {}).get('title', 'Unnamed API')

    def get_base_url(self) -> str:
        servers = self.data.get('servers', [])
        return servers[0]['url'] if servers else ''

    def get_version(self) -> str:
        return self.data.get('info', {}).get('version', '1.0.0')
