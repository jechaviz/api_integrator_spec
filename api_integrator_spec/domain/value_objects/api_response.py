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
