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

    def test_getattr_method_nonexistent_attribute(self):
        with pytest.raises(AttributeError):
            self.api_response.nonexistent_attribute

    def test_str_method(self):
        expected_str = f"ApiResponse(status_code=200, body={self.mock_response.text}...)"
        assert str(self.api_response) == expected_str

    def test_print_api_response(self, capsys):
        print(self.api_response)
        captured = capsys.readouterr()
        expected_output = f"ApiResponse(status_code=200, body={self.mock_response.text}...)\n"
        assert captured.out == expected_output
