import requests

class ApiResponse:
    def __init__(self, response: requests.Response):
        self.response = response
        self.status_code = response.status_code
        self.headers = response.headers
        self.url = response.url
        self.request = response.request
        self.encoding = response.encoding
        self.cookies = response.cookies
        self.body= response.text
        self.json = response.json()

    def __getattr__(self, name: str):
        return getattr(self.response, name)

    def __str__(self) -> str:
        return f"ApiResponse(status_code={self.status_code}, body={self.body[:100]})"
