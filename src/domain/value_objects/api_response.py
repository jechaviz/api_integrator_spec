import json
import requests
import xml.etree.ElementTree as ET
import xmltodict

class ApiResponse:
    def __init__(self, response: requests.Response):
        self.response = response
        self.status_code = response.status_code
        self.headers = response.headers
        self.url = response.url
        self.request = response.request
        self.encoding = response.encoding
        self.cookies = response.cookies
        self.body = response.text
        self.json = None
        self.xml = None
        self._parse_content()

    def _parse_content(self):
        content_type = self.headers.get('Content-Type', '').lower()
        if 'application/json' in content_type:
            try:
                self.json = self.response.json()
            except json.JSONDecodeError:
                pass
        elif 'application/xml' in content_type or 'text/xml' in content_type:
            try:
                self.xml = ET.fromstring(self.body)
                self.json = xmltodict.parse(self.body)
            except ET.ParseError:
                pass

    def __getattr__(self, name: str):
        return getattr(self.response, name)

    def __str__(self) -> str:
        elements = [f"status_code={self.status_code}"]
        
        headers_str = self._format_headers()
        elements.append(f"headers={{{headers_str}}}")
        
        body_str = self._format_body()
        elements.append(body_str)
        
        for attr in ['url', 'encoding']:
            value = self._format_attribute(attr)
            elements.append(f"{attr}={value}")
        
        return f"ApiResponse({', '.join(elements)})"

    def _format_headers(self) -> str:
        if isinstance(self.headers, dict):
            return ', '.join(f"{k}={v}" for k, v in self.headers.items())
        elif isinstance(self.headers, list):
            return ', '.join(f"{h[0]}={h[1]}" for h in self.headers)
        else:
            return self._format_attribute('headers')

    def _format_body(self) -> str:
        if self.json is not None:
            body_str = json.dumps(self.json)[:100]
            return f"body(json)={body_str}"
        else:
            body_str = str(self.body)[:100]
            return f"body(text)={body_str}"

    def _format_attribute(self, attr: str) -> str:
        value = getattr(self, attr)
        if hasattr(value, '__repr__'):
            return value.__repr__()
        return str(value)
