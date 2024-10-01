import yaml
from api_integrator_spec.domain.value_objects.yaml_object import YamlObject

class ApiConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.api_name = config_path.replace('.yml', '')
        self.api = self._load_config()
        self.var_defaults = self.api.vars
        self.constants = self.api.constants

    def _load_config(self):
        with open(self.config_path) as f:
            data = yaml.safe_load(f)
            return YamlObject(data)
