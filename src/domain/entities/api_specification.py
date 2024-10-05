from typing import List, Dict, Any, Optional
from src.domain.exceptions.endpoint_not_found_exception import EndpointNotFoundException

class ApiSpecification:
    def __init__(self, name: str, base_url: str, version: str, servers: List[Dict[str, Any]] = None, info: Dict[str, Any] = None):
        self.name = name
        self.base_url = base_url
        self.version = version
        self.endpoints: List[Dict[str, Any]] = []
        self.schemas: Dict[str, Any] = {}
        self.security_schemes: Dict[str, Any] = {}
        self.webhooks: Dict[str, Any] = {}
        self.servers: List[Dict[str, Any]] = servers or []
        self.tags: List[Dict[str, Any]] = []
        self.external_docs: Dict[str, Any] = {}
        self.info: Dict[str, Any] = info or {}
        self.responses: Dict[str, Any] = {}
        self.parameters: Dict[str, Any] = {}
        self.examples: Dict[str, Any] = {}
        self.request_bodies: Dict[str, Any] = {}
        self.headers: Dict[str, Any] = {}
        self.links: Dict[str, Any] = {}
        self.callbacks: Dict[str, Any] = {}
        self.path_items: Dict[str, Any] = {}
        self.security_requirements: List[Dict[str, List[str]]] = []

    def get_name(self) -> str:
        return self.name

    def get_base_url(self) -> str:
        return self.base_url

    def get_version(self) -> str:
        return self.version

    def get_endpoints(self) -> List[Dict[str, Any]]:
        return self.endpoints

    def add_endpoint(self, endpoint: Dict[str, Any]) -> None:
        self.endpoints.append(endpoint)

    def get_endpoint(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        for endpoint in self.endpoints:
            if endpoint['path'] == path and endpoint['method'] == method:
                return endpoint
        return None

    def get_sample_responses_for_endpoint(self, path: str, method: str) -> Dict[str, Any]:
        endpoint = self.get_endpoint(path, method)
        if endpoint and 'responses' in endpoint:
            return endpoint['responses']
        return {}

    def get_response_by_status_code(self, path: str, method: str, status_code: str) -> Optional[Dict[str, Any]]:
        endpoint = self.get_endpoint(path, method)
        if endpoint and 'responses' in endpoint and status_code in endpoint['responses']:
            return endpoint['responses'][status_code]
        return None

    def set_schemas(self, schemas: Dict[str, Any]) -> None:
        self.schemas = schemas

    def set_security_schemes(self, security_schemes: Dict[str, Any]) -> None:
        self.security_schemes = security_schemes

    def set_webhooks(self, webhooks: Dict[str, Any]) -> None:
        self.webhooks = webhooks

    def set_servers(self, servers: List[Dict[str, Any]]) -> None:
        self.servers = servers

    def set_tags(self, tags: List[Dict[str, Any]]) -> None:
        self.tags = tags

    def set_external_docs(self, external_docs: Dict[str, Any]) -> None:
        self.external_docs = external_docs

    def set_responses(self, responses: Dict[str, Any]) -> None:
        self.responses = responses

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        self.parameters = parameters

    def set_examples(self, examples: Dict[str, Any]) -> None:
        self.examples = examples

    def set_request_bodies(self, request_bodies: Dict[str, Any]) -> None:
        self.request_bodies = request_bodies

    def set_headers(self, headers: Dict[str, Any]) -> None:
        self.headers = headers

    def set_links(self, links: Dict[str, Any]) -> None:
        self.links = links

    def set_callbacks(self, callbacks: Dict[str, Any]) -> None:
        self.callbacks = callbacks

    def set_path_items(self, path_items: Dict[str, Any]) -> None:
        self.path_items = path_items

    def set_security_requirements(self, security_requirements: List[Dict[str, List[str]]]) -> None:
        self.security_requirements = security_requirements

    def add_request_body_to_endpoint(self, path: str, method: str, request_body: Dict[str, Any]) -> None:
        self._update_endpoint(path, method, {'requestBody': request_body})

    def add_response_to_endpoint(self, path: str, method: str, status_code: str, response: Dict[str, Any]) -> None:
        self._update_endpoint(path, method, {'responses': {status_code: response}})

    def add_security_to_endpoint(self, path: str, method: str, security: List[Dict[str, List[str]]]) -> None:
        self._update_endpoint(path, method, {'security': security})

    def add_tag_to_endpoint(self, path: str, method: str, tag: str) -> None:
        endpoint = self.get_endpoint(path, method)
        if endpoint is None:
            raise EndpointNotFoundException(f"Endpoint not found for path: {path} and method: {method}")
        if 'tags' not in endpoint:
            endpoint['tags'] = []
        if tag not in endpoint['tags']:
            endpoint['tags'].append(tag)
            self._update_endpoint(path, method, {'tags': endpoint['tags']})

    def set_endpoint_summary(self, path: str, method: str, summary: str) -> None:
        self._update_endpoint(path, method, {'summary': summary})

    def set_endpoint_description(self, path: str, method: str, description: str) -> None:
        self._update_endpoint(path, method, {'description': description})

    def get_sample_responses_by_status_code(self, path: str, method: str, status_code: str) -> Dict[str, Any]:
        endpoint = self.get_endpoint(path, method)
        if endpoint is None:
            raise EndpointNotFoundException(f"Endpoint not found for path: {path} and method: {method}")

        if 'responses' not in endpoint or status_code not in endpoint['responses']:
            return {}

        response = endpoint['responses'][status_code]
        return response.get('examples', {})

    def _update_endpoint(self, path: str, method: str, data: Dict[str, Any]) -> None:
        endpoint = self.get_endpoint(path, method)
        if endpoint is None:
            raise EndpointNotFoundException(f"Endpoint not found for path: {path} and method: {method}")

        for key, value in data.items():
            if isinstance(value, dict) and key in endpoint and isinstance(endpoint[key], dict):
                endpoint[key].update(value)
            else:
                endpoint[key] = value

        self.endpoints = [e if e['path'] != path or e['method'] != method else endpoint for e in self.endpoints]
