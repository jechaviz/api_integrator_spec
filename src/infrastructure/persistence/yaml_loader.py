import yaml
from api_integrator_spec.domain.value_objects.yaml_object import YamlObject

class YamlLoader:
    @staticmethod
    def load(config_path):
        with open(config_path) as f:
            data = yaml.safe_load(f)
            return YamlObject(data)
