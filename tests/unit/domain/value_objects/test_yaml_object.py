import snoop
import pytest
import yaml
from pathlib import Path
from api_integrator_spec.domain.value_objects.yml_obj import YmlObj


class TestYmlObj:
    @pytest.fixture(autouse=True)
    def setup(self):
        config_path = Path.cwd().parent.parent.parent.parent / 'api_integrator_spec/infrastructure/config/api_parser_conf.yml'
        with open(config_path, 'r') as f:
            self.conf = YmlObj(yaml.safe_load(f))

    def test_top_level_attributes(self):
        assert self.conf.api_integrator == "0.0.1"
        assert isinstance(self.conf.info, YmlObj)
        assert isinstance(self.conf.supplier_servers, list)
        assert isinstance(self.conf.tags, list)
        assert isinstance(self.conf.actions, YmlObj)
        assert isinstance(self.conf.vars, YmlObj)
        assert isinstance(self.conf.constants, YmlObj)

    def test_nested_attributes(self):
        assert self.conf.info.title == "Interaction Configuration with API from My Supplier to integrate with my app"
        assert self.conf.info.version == "1.0.0"
        assert self.conf.info.contact.name == "Developer"

    def test_list_access(self):
        assert len(self.conf.supplier_servers) == 2
        assert self.conf.supplier_servers[0].id == "prod"
        assert self.conf.supplier_servers[1].url == "https://sandbox.api.my.supplier.com"

    def test_nested_list_access(self):
        assert len(self.conf.actions.auth.performs) == 1
        assert self.conf.actions.auth.performs[0].perform.type == "http.post"
        assert self.conf.actions.auth.performs[0].perform.data.path == "{{supplier_server.url}}/auth/login"

    def test_get_method(self):
        assert self.conf.get('info.title') == "Interaction Configuration with API from My Supplier to integrate with my app"
        assert self.conf.get('actions.auth.performs.0.perform.type') == "http.post"
        assert self.conf.get('non_existent_key', 'default') == 'default'

    def test_has_method(self):
        assert self.conf.has('info.title')
        assert self.conf.has('actions.auth.performs.0.perform.type')
        assert not self.conf.has('non_existent_key')

    def test_to_dict_method(self):
        assert isinstance(self.conf.to_dict(), dict)
        assert self.conf.to_dict()['api_integrator'] == "0.0.1"

    def test_iteration(self):
        keys = list(self.conf.keys())
        print(keys)
        assert 'api_integrator' in keys
        assert 'info' in keys
        assert 'actions' in keys

        for key, value in self.conf.items():
            if (self.conf.get(key) != value):
                print(key, value)
                print(key,self.conf.get(key))


    def test_bool(self):
        assert bool(self.conf) is True
        assert bool(YmlObj({})) is False

    @snoop
    def test_nested_perform_structure(self):
        perform = self.conf.actions.auth.performs[0].perform
        assert isinstance(perform, YmlObj)
        assert perform.type == "http.post"
        assert perform._data.path == "{{supplier_server.url}}/auth/login"
        assert perform._data.body.user == "{{user}}"
        assert perform._data.body['pass'] == "{{pass}}"
