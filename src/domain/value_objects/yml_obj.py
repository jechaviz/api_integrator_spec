class YmlObj:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data

    def __getattr__(self, key):
        if key in self._data:
            value = self._data[key]
            if isinstance(value, dict):
                return YmlObj(value)
            elif isinstance(value, list):
                return [YmlObj(item) if isinstance(item, dict) else item for item in value]
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
            elif isinstance(value, list) and k.isdigit():
                index = int(k)
                if 0 <= index < len(value):
                    value = value[index]
                else:
                    return default
            else:
                return default
        return YmlObj(value) if isinstance(value, dict) else value

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
        return [YmlObj(value) if isinstance(value, dict) else value for value in self._data.values()]

    def items(self):
        return [(key, YmlObj(value) if isinstance(value, dict) else value) for key, value in self._data.items()]

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return self.has(key)

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return f"YmlObj({self._data})"

    def __setitem__(self, key, value):
        if isinstance(self._data, dict):
            self._data[key] = value
        else:
            raise TypeError("This YmlObj does not support item assignment")

    def __getitem__(self, key):
        if isinstance(self._data, dict):
            value = self._data[key]
            return YmlObj(value) if isinstance(value, dict) else value
        elif isinstance(self._data, list):
            return YmlObj(self._data[key]) if isinstance(self._data[key], dict) else self._data[key]
        else:
            raise TypeError("This YmlObj does not support item access")

    def update(self, other):
        if isinstance(self._data, dict):
            if isinstance(other, dict):
                self._data.update(other)
            elif isinstance(other, YmlObj):
                self._data.update(other.to_dict())
            else:
                raise TypeError("Update only supports dict or YmlObj")
        else:
            raise TypeError("This YmlObj does not support update")
