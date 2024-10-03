import pytest
from unittest.mock import Mock
from api_integrator_spec.domain.value_objects.api_response import ApiResponse

class TestApiResponse:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_response = Mock()
        self.mock_response.text = '{"key": "value"}'
        self.mock_response.json.return_value = {"key": "value"}
        self.mock_response.status_code = 200
        self.api_response = ApiResponse(self.mock_response)

    def test_body_property(self):
        assert self.api_response.body == '{"key": "value"}'

    def test_json_property(self):
        assert self.api_response.json == {"key": "value"}

    def test_getattr_method(self):
        assert self.api_response.status_code == 200

    def test_str_method(self):
        expected_str = f"ApiResponse(status_code=200, headers={{{self.mock_response.headers!r}}}, body(json)={{'key': 'value'}}, url={self.mock_response.url!r}, encoding={self.mock_response.encoding!r})"
        assert str(self.api_response) == expected_str

    def test_print_api_response(self, capsys):
        captured = capsys.readouterr()
        expected_output = f"ApiResponse(status_code=200, headers={{{self.mock_response.headers!r}}}, body(json)={{'key': 'value'}}, url={self.mock_response.url!r}, encoding={self.mock_response.encoding!r})\n"
        assert captured.out == expected_output

    def test_str_method_with_text_response(self):
        self.mock_response.text = 'This is a text response'
        self.mock_response.json.side_effect = ValueError
        self.api_response = ApiResponse(self.mock_response)
        expected_str = f"ApiResponse(status_code=200, headers={{}}, body(text)=This is a text response, url=mock://test.com, encoding=utf-8)"
        assert str(self.api_response) == expected_str

