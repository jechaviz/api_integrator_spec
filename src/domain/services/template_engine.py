import re
import json
from typing import Any, Union
from src.domain.value_objects.obj_utils import Obj

class TemplateEngine:
    def __init__(self, vars_connector, response_handler):
        self.vars_connector = vars_connector
        self.response_handler = response_handler
        
    def render(self, template: Union[str, Obj, list], params: Obj) -> Any:
        if isinstance(template, str):
            return self._render_string(template, params)
        elif isinstance(template, Obj):
            return Obj({k: self.render(v, params) for k, v in template.items()})
        elif isinstance(template, list):
            return [self.render(item, params) for item in template]
        return template
        
    def _render_string(self, template: str, params: Obj) -> str:
        return re.sub(
            r'\{\{(.+?)\}\}',
            lambda m: self._get_value(m.group(1).strip(), params),
            template
        )
        
    def _get_value(self, key: str, params: Obj) -> str:
        if key.startswith('response.'):
            return str(self.response_handler.get_value(key))
        
        value = self.vars_connector.get_value(key, params)
        if isinstance(value, dict):
            return json.dumps(value)
        return str(value)
