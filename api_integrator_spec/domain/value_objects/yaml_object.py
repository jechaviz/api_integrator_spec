class YamlObject:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data

    def __getattr__(self, key):
        if key in self._data:
            value = self._data[key]
            if isinstance(value, dict):
                return YamlObject(value)
            elif isinstance(value, list):
                return [YamlObject(item) if isinstance(item, dict) else item for item in value]
            else:
                return value
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")

    def __iter__(self):
        return iter(self._data.items())

    def __bool__(self):
        return bool(self._data)

    def get(self, key, default=None):
        keys = key.split('.')
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return YamlObject(value) if isinstance(value, dict) else value

    def has(self, key):
        keys = key.split('.')
        value = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False
        return True

    def keys(self):
        return self._data.keys()

    def values(self):
        return [YamlObject(value) if isinstance(value, dict) else value for value in self._data.values()]

    def items(self):
        return [(key, YamlObject(value) if isinstance(value, dict) else value) for key, value in self._data.items()]

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return self.has(key)
