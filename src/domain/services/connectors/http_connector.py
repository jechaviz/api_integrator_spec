from typing import Any, Dict
from src.domain.interfaces.connector_i import ConnectorI
from src.domain.value_objects.api_response import ApiResponse

class HttpConnector(ConnectorI):
    def __init__(self, api_integrator):
        self.api = api_integrator
        
    def execute(self, command: str, data: Any, params: Dict) -> ApiResponse:
        """Execute HTTP requests"""
        method = command.split('.')[1].upper()
        url = self.api._prepare_url(data, params)
        headers_dict = self.api._prepare_headers(data, params)
        query_dict = self.api._prepare_query(data, params)
        body_data = data.get('body', {})

        if data.get('type') == 'bulk':
            return self.api._handle_bulk_request(method, url, body_data, headers_dict, data, params)
        else:
            return self.api._handle_single_request(method, url, body_data, headers_dict, query_dict, data, params)
