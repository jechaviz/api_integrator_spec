import pytest
import yaml
from pathlib import Path
from api_integrator_spec.domain.value_objects.yaml_object import YamlObject

class TestYamlObject:
    @pytest.fixture(autouse=True)
    def setup(self):
        config_path = Path(__file__).parent.parent / 'infrastructure' / 'config' / 'api_parser_conf.yml'
        with open(config_path, 'r') as f:
            self.yaml_config = YamlObject(yaml.safe_load(f))

    def test_top_level_attributes(self):
        assert self.yaml_config.api_integrator == "0.0.1"
        assert isinstance(self.yaml_config.info, YamlObject)
        assert isinstance(self.yaml_config.supplier_servers, list)
        assert isinstance(self.yaml_config.tags, list)
        assert isinstance(self.yaml_config.actions, YamlObject)
        assert isinstance(self.yaml_config.vars, YamlObject)
        assert isinstance(self.yaml_config.constants, YamlObject)

    def test_nested_attributes(self):
        assert self.yaml_config.info.title == "Interaction Configuration with API from My Supplier to integrate with my app"
        assert self.yaml_config.info.version == "1.0.0"
        assert self.yaml_config.info.contact.name == "Developer"

    def test_list_access(self):
        assert len(self.yaml_config.supplier_servers) == 2
        assert self.yaml_config.supplier_servers[0].id == "prod"
        assert self.yaml_config.supplier_servers[1].url == "https://sandbox.api.my.supplier.com"

    def test_deep_nested_access(self):
        assert self.yaml_config.actions.auth.performs[0].perform == "http.post"
        assert self.yaml_config.actions.auth.performs[0].data.path == "{{supplier_server.url}}/auth/login"

    def test_get_method(self):
        assert self.yaml_config.get('info.title') == "Interaction Configuration with API from My Supplier to integrate with my app"
        assert self.yaml_config.get('actions.auth.performs.0.perform') == "http.post"
        assert self.yaml_config.get('non_existent_key', 'default') == 'default'

    def test_has_method(self):
        assert self.yaml_config.has('info.title')
        assert self.yaml_config.has('actions.auth.performs.0.perform')
        assert not self.yaml_config.has('non_existent_key')

    def test_to_dict_method(self):
        assert isinstance(self.yaml_config.to_dict(), dict)
        assert self.yaml_config.to_dict()['api_integrator'] == "0.0.1"

    def test_iteration(self):
        keys = list(self.yaml_config.keys())
        assert 'api_integrator' in keys
        assert 'info' in keys
        assert 'actions' in keys

        for key, value in self.yaml_config.items():
            assert self.yaml_config.get(key) == value

    def test_bool(self):
        assert bool(self.yaml_config) is True
        assert bool(YamlObject({})) is False

if __name__ == '__main__':
    pytest.main([__file__])
