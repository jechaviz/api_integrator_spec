import yaml
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Obj:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._recursive_to_dict(self._data)

    def _recursive_to_dict(self, data):
        if isinstance(data, dict):
            return {k: self._recursive_to_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._recursive_to_dict(item) for item in data]
        elif isinstance(data, Obj):
            return self._recursive_to_dict(data._data)
        else:
            return data

    def __getattr__(self, key):
        if key in self._data:
            value = self._data[key]
            if isinstance(value, dict):
                return Obj(value)
            elif isinstance(value, list):
                return [Obj(item) if isinstance(item, dict) else item for item in value]
            else:
                return value
        else:
            raise AttributeError(f"'{self.keys()}' has no key '{key}\nIn: {self._data}'")

    def __iter__(self):
        return iter(self._data.items())

    def __bool__(self):
        return bool(self._data)

    def get(self, key, default=None):
        keys = key.replace('[', '.').replace(']', '').split('.')
        value = self._data
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                elif isinstance(value, list) and k.isdigit():
                    value = value[int(k)]
                else:
                    return default
            return Obj(value) if isinstance(value, dict) else value
        except (KeyError, IndexError, TypeError):
            return default

    def has(self, key):
        keys = key.split('.')
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            elif isinstance(value, list) and k.isdigit():
                index = int(k)
                if 0 <= index < len(value):
                    value = value[index]
                else:
                    return False
            else:
                return False
        return True

    def keys(self):
        return self._data.keys()

    def values(self):
        return [Obj(value) if isinstance(value, dict) else value for value in self._data.values()]

    def items(self):
        return [(key, Obj(value) if isinstance(value, dict) else value) for key, value in self._data.items()]

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return self.has(key)

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return f"Obj({self._data})"

    def __setitem__(self, key, value):
        if isinstance(self._data, dict):
            self._data[key] = value
        else:
            raise TypeError("This Obj does not support item assignment")

    def __getitem__(self, key):
        if isinstance(self._data, dict):
            value = self._data[key]
            return Obj(value) if isinstance(value, dict) else value
        elif isinstance(self._data, list):
            return Obj(self._data[key]) if isinstance(self._data[key], dict) else self._data[key]
        else:
            raise TypeError("This Obj does not support item access")

    def update(self, other):
        if isinstance(self._data, dict):
            if isinstance(other, dict):
                self._data.update(other)
            elif isinstance(other, Obj):
                self._data.update(other.to_dict())
            else:
                raise TypeError("Update only supports dict or Obj")
        else:
            raise TypeError("This Obj does not support update")

    def save(self, file_path: str):
        class OrderedDumper(yaml.SafeDumper):
            def ignore_aliases(self, data):
                return True

            def represent_mapping(self, tag, mapping, flow_style=None):
                return yaml.SafeDumper.represent_mapping(self, tag, mapping, flow_style)

        output_file = Path(file_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            yaml.dump(self.to_dict(), f, Dumper=OrderedDumper, sort_keys=False, default_flow_style=False)

    @classmethod
    def from_yaml(cls, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            return cls(data)
        except FileNotFoundError:
            logger.error(f"YAML file not found: {file_path}")
            return cls({})
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            return cls({})
