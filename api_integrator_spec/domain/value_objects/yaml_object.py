class YamlObject:
  def __init__(self, data):
    self.data = data

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