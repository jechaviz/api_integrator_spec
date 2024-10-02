import pytest
from pathlib import Path
from api_integrator_spec.domain.value_objects.yaml_object import YamlObject

@pytest.fixture
def yaml_config():
    config_path = Path(__file__).parent.parent / 'infrastructure' / 'config' / 'api_parser_conf.yml'
    with open(config_path, 'r') as f:
        return YamlObject(yaml.safe_load(f))

def test_yaml_object_top_level_attributes(yaml_config):
    assert yaml_config.api_integrator == "0.0.1"
    assert isinstance(yaml_config.info, YamlObject)
    assert isinstance(yaml_config.supplier_servers, list)
    assert isinstance(yaml_config.tags, list)
    assert isinstance(yaml_config.actions, YamlObject)
    assert isinstance(yaml_config.vars, YamlObject)
    assert isinstance(yaml_config.constants, YamlObject)

def test_yaml_object_nested_attributes(yaml_config):
    assert yaml_config.info.title == "Interaction Configuration with API from My Supplier to integrate with my app"
    assert yaml_config.info.version == "1.0.0"
    assert yaml_config.info.contact.name == "Developer"

def test_yaml_object_list_access(yaml_config):
    assert len(yaml_config.supplier_servers) == 2
    assert yaml_config.supplier_servers[0].id == "prod"
    assert yaml_config.supplier_servers[1].url == "https://sandbox.api.my.supplier.com"

def test_yaml_object_deep_nested_access(yaml_config):
    assert yaml_config.actions.auth.performs[0].perform == "http.post"
    assert yaml_config.actions.auth.performs[0].data.path == "{{supplier_server.url}}/auth/login"

def test_yaml_object_get_method(yaml_config):
    assert yaml_config.get('info.title') == "Interaction Configuration with API from My Supplier to integrate with my app"
    assert yaml_config.get('actions.auth.performs.0.perform') == "http.post"
    assert yaml_config.get('non_existent_key', 'default') == 'default'

def test_yaml_object_has_method(yaml_config):
    assert yaml_config.has('info.title')
    assert yaml_config.has('actions.auth.performs.0.perform')
    assert not yaml_config.has('non_existent_key')

def test_yaml_object_to_dict_method(yaml_config):
    assert isinstance(yaml_config.to_dict(), dict)
    assert yaml_config.to_dict()['api_integrator'] == "0.0.1"

def test_yaml_object_iteration(yaml_config):
    keys = list(yaml_config.keys())
    assert 'api_integrator' in keys
    assert 'info' in keys
    assert 'actions' in keys

    for key, value in yaml_config.items():
        assert yaml_config.get(key) == value

def test_yaml_object_bool(yaml_config):
    assert bool(yaml_config) is True
    assert bool(YamlObject({})) is False

if __name__ == '__main__':
    pytest.main([__file__])
