import pytest
from unittest.mock import patch, MagicMock
from api_integrator_spec.domain.services.api_integrator import ApiIntegrator
from api_integrator_spec.domain.value_objects.yml_obj import YmlObj
from api_integrator_spec.domain.value_objects.api_response import ApiResponse

class TestApiIntegrator:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.config_path = 'infrastructure/config/jsonplaceholder_conf.yml'
        self.integrator = ApiIntegrator(self.config_path)

    def test_config_loading(self):
        assert isinstance(self.integrator.config, YmlObj)
        assert self.integrator.config.api_integrator == '0.0.1'
        assert self.integrator.config.info.title == 'Interaction Configuration with API from My Supplier to integrate with my app'
        assert len(self.integrator.config.supplier_servers) == 2
        assert len(self.integrator.config.tags) == 2
        assert len(self.integrator.config.actions) == 2

    def test_vars_and_constants(self):
        assert self.integrator.vars.user == 'user'
        assert self.integrator.vars.get('pass') == 'pass'
        assert self.integrator.vars.supplier_server.id == 'sandbox'
        assert self.integrator.vars.my_app_api_token == 'your_app_token_here'
        assert self.integrator.constants.retry_trials == 3

    @patch('requests.Session.request')
    def test_auth_action_success(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'ok'
        mock_response.json.return_value = {'token': 'test_token'}
        mock_request.return_value = mock_response
        with patch.object(self.integrator, '_handle_log') as mock_log:
            self.integrator.perform_action('auth')

        mock_request.assert_called_once_with(
            'POST',
            'https://sandbox.api.my.supplier.com/auth/login',
            headers={},
            data='{"user": "user", "pass": "pass"}',
            params={}
        )
        assert self.integrator.vars.session_token == 'test_token'
        mock_log.assert_called_with('log.info', YmlObj({'data': 'Successfully authenticated'}),
                                    {'response': mock_response})

    @patch('requests.Session.request')
    def test_auth_action_error(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'error'
        mock_request.return_value = mock_response

        with patch.object(self.integrator, '_handle_log') as mock_log:
            self.integrator.perform_action('auth')

        mock_log.assert_any_call('log.debug', YmlObj({'data': 'error'}), {'response': mock_response})
        mock_log.assert_any_call('log.error', YmlObj({'data': 'Error authenticating'}), {'response': mock_response})

    @patch('requests.Session.request')
    def test_get_item_part_success(self, mock_request):
        self.integrator.vars.session_token = 'test_token'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'ok'
        mock_response.json.return_value = {
            'id': '123',
            'name': 'Test Item',
            'price': 10.99,
            'description': 'Test Description',
            'stock': 100,
            'img': 'test.jpg',
            'is_active': True
        }
        mock_request.return_value = mock_response

        with patch.object(self.integrator, '_handle_log') as mock_log, \
             patch.object(self.integrator, '_handle_http') as mock_http:
            self.integrator.perform_action('get_item_part', {'id_item': '123', 'id_part': '456'})

        mock_request.assert_called_once_with(
            'GET',
            'https://sandbox.api.my.supplier.com/items/part/123/part/456',
            headers={'Authorization': 'Bearer test_token'},
            data='{}',
            params={}
        )
        mock_log.assert_called_with('log.info', YmlObj({'data': 'Successfully got item part'}), {'response': mock_response, 'id_item': '123', 'id_part': '456'})
        mock_http.assert_called_with('http.post', YmlObj({
            'data': {
                'url': 'https://api.my.app.com/items/part/{{id}}',
                'headers': {'Authorization': 'Bearer {{my_app_api_token}}'},
                'body': {
                    'id': 'response.id',
                    'name': 'response.name',
                    'price': 'response.price',
                    'description': 'response.description',
                    'stock': 'response.stock',
                    'image': 'response.img',
                    'is_active': 'response.is_active'
                }
            }
        }), {'response': mock_response, 'id_item': '123', 'id_part': '456'})

    @patch('requests.Session.request')
    def test_get_item_part_error(self, mock_request):
        self.integrator.vars.session_token = 'test_token'
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'error'
        mock_request.return_value = mock_response

        with patch.object(self.integrator, '_handle_log') as mock_log:
            self.integrator.perform_action('get_item_part', {'id_item': '123', 'id_part': '456'})

        mock_log.assert_called_with('log.error', YmlObj({'data': 'Error getting item part: response.body'}), {'response': mock_response, 'id_item': '123', 'id_part': '456'})