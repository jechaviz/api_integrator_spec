import requests
import json

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
        try:
            self.json = response.json()
        except json.JSONDecodeError:
            self.json = None

    def __getattr__(self, name: str):
        return getattr(self.response, name)

    def __str__(self) -> str:
        elements = [f"status_code={self.status_code}"]
        
        # Incluir headers
        headers_str = self._format_headers()
        elements.append(f"headers={{{headers_str}}}")
        
        # Comprobar si el cuerpo es JSON o texto
        body_str = self._format_body()
        elements.append(body_str)
        
        # Incluir otros atributos dinámicamente
        for attr in ['url', 'encoding']:
            value = getattr(self, attr)
            elements.append(f"{attr}={value}")
        
        return f"ApiResponse({', '.join(elements)})"

    def _format_headers(self) -> str:
        if isinstance(self.headers, dict):
            return ', '.join(f"{k}={v}" for k, v in self.headers.items())
        elif isinstance(self.headers, list):
            return ', '.join(f"{h[0]}={h[1]}" for h in self.headers)
        else:
            return str(self.headers)

    def _format_body(self) -> str:
        if self.json is not None:
            body_str = json.dumps(self.json)[:100]  # Limitar a 100 caracteres
            return f"body(json)={body_str}"
        else:
            body_str = str(self.body)[:100]  # Limitar a 100 caracteres
            return f"body(text)={body_str}"
