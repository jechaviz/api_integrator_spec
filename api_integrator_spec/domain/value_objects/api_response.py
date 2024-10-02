class ApiResponse:
    def __init__(self, response_data):
        self.response_data = response_data

    def __getattr__(self, name):
        return self.response_data.get(name, None)

    def __repr__(self):
        return str(self.response_data)
import requests

class ApiResponse:
    def __init__(self, response: requests.Response):
        self.response = response

    @property
    def body(self):
        return self.response.text

    @property
    def json(self):
        return self.response.json()

    def __getattr__(self, name: str):
        return getattr(self.response, name)
