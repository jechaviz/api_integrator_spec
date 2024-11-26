from pathlib import Path
from src.domain.value_objects.obj_utils import Obj

class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        
    def load(self) -> Obj:
        """Load and merge all configuration files"""
        config = Obj.from_yaml(self.config_path)
        
        # Load additional configs if specified
        if config.has('include'):
            for include_path in config.include:
                include_config = Obj.from_yaml(
                    self.config_path.parent / include_path
                )
                config.update(include_config)
                
        return config
