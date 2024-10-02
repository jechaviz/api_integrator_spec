class YamlObject:
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, YamlObject(value))
            else:
                setattr(self, key, value)

    def __getattr__(self, name):
        return None

    def __repr__(self):
        return str(self.__dict__)
