import pytest
import yaml
import snoop
from pathlib import Path
from src.domain.value_objects.yml_obj import YmlObj

class TestYmlObj:
    @pytest.fixture(autouse=True)
    def setup(self):
        config_path = Path(__file__).parent.parent.parent.parent.parent / 'infrastructure' / 'config' / 'jsonplaceholder_conf.yml'
        with open(config_path, 'r') as f:
            self.yaml_config = YmlObj(yaml.safe_load(f))

    @snoop
    def test_top_level_attributes(self):
        assert self.yaml_config.api_integrator == "0.0.1"
        assert isinstance(self.yaml_config.info, YmlObj)
        assert isinstance(self.yaml_config.supplier_servers, list)
        assert isinstance(self.yaml_config.tags, list)
        assert isinstance(self.yaml_config.actions, YmlObj)
        assert isinstance(self.yaml_config.vars, YmlObj)
        assert isinstance(self.yaml_config.constants, YmlObj)

    @snoop
    def test_nested_attributes(self):
        assert self.yaml_config.info.title == "Interaction Configuration with API from My Supplier to integrate with my app"
        assert self.yaml_config.info.version == "1.0.0"
        assert self.yaml_config.info.contact.name == "Developer"

    @snoop
    def test_list_access(self):
        assert len(self.yaml_config.supplier_servers) == 2
        assert self.yaml_config.supplier_servers[0].id == "prod"
        assert self.yaml_config.supplier_servers[1].url == "https://sandbox.api.my.supplier.com"

    @snoop
    def test_deep_nested_access(self):
        assert self.yaml_config.actions.auth.performs[0].perform.type == "http.post"
        assert self.yaml_config.actions.auth.performs[0].perform._data.path == "{{supplier_server.url}}/auth/login"

    @snoop
    def test_get_method(self):
        assert self.yaml_config.get('info.title') == "Interaction Configuration with API from My Supplier to integrate with my app"
        assert self.yaml_config.get('actions.auth.performs.0.perform.type') == "http.post"
        assert self.yaml_config.get('non_existent_key', 'default') == 'default'

    @snoop
    def test_has_method(self):
        assert self.yaml_config.has('info.title')
        assert self.yaml_config.has('actions.auth.performs.0.perform.type')
        assert not self.yaml_config.has('non_existent_key')

    @snoop
    def test_nested_perform_structure(self):
        perform = self.yaml_config.actions.auth.performs[0].perform
        assert isinstance(perform, YmlObj)
        assert perform.type == "http.post"
        assert perform._data.path == "{{supplier_server.url}}/auth/login"
        assert perform._data.body.user == "{{user}}"
        assert perform._data.body['pass'] == "{{pass}}"

    @snoop
    def test_to_dict_method(self):
        assert isinstance(self.yaml_config.to_dict(), dict)
        assert self.yaml_config.to_dict()['api_integrator'] == "0.0.1"

    @snoop
    def test_iteration(self):
        keys = list(self.yaml_config.keys())
        assert 'api_integrator' in keys
        assert 'info' in keys
        assert 'actions' in keys

        for key, value in self.yaml_config.items():
            assert self.yaml_config.get(key) == value

    @snoop
    def test_bool(self):
        assert bool(self.yaml_config) is True
        assert bool(YmlObj({})) is False

    @snoop
    def test_str_and_repr(self):
        yml_obj = YmlObj({"key": "value"})
        assert str(yml_obj) == "{'key': 'value'}"
        assert repr(yml_obj) == "YmlObj({'key': 'value'})"
