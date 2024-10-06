import yaml
from src.domain.value_objects.yml_obj import YmlObj

class YmlLoader:
    @staticmethod
    def load(config_path):
        with open(config_path) as f:
            data = yaml.safe_load(f)
            return YmlObj(data)
