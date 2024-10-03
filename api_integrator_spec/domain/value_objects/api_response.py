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

    def __str__(self) -> str:
        return f"ApiResponse(status_code={self.status_code}, body={self.body[:100]}...)"

    # Keep the to_string method for backward compatibility
    def to_string(self) -> str:
        return str(self)
