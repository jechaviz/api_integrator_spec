class YamlObject:
    def __init__(self, data):
        self.data = data

    def to_dict(self):
        return self.data

    def __getattr__(self, key):
        if key in self.data:
            value = self.data[key]
            if isinstance(value, dict):
                return YamlObject(value)
            elif isinstance(value, list):
                return [YamlObject(item) if isinstance(item, dict) else item for item in value]
            else:
                return value
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")

    def __iter__(self):
        return iter(self.data.items())

    def __bool__(self):
        return bool(self.data)

    def get(self, key, default=None):
        return getattr(self, key, default)
