import json
import logging
import re
from typing import Any, List, Union
from src.domain.value_objects.obj_utils import Obj

class ResponseHandler:
    def __init__(self):
        self.latest_response = None
        
    def set_response(self, response):
        self.latest_response = response
        
    def get_value(self, key: str) -> Any:
        if not self.latest_response:
            return None
            
        response_key = key[9:]  # Remove 'response.' prefix
        
        if hasattr(self.latest_response, response_key):
            return getattr(self.latest_response, response_key)
            
        try:
            return self._get_json_value(response_key)
        except Exception as e:
            logging.warning(f'Error accessing response value: {e}')
            return None
            
    def check_conditions(self, conditions: Obj) -> bool:
        """Check if response matches given conditions"""
        if not self.latest_response:
            return False
            
        condition_checks = {
            'code': lambda v: self.latest_response.status_code == v,
            'contains': lambda v: v in self.latest_response.text,
            'has_value': lambda v: bool(self.latest_response.text) == v,
            'matches': lambda v: re.search(v, self.latest_response.text) is not None,
            'has_key': lambda v: v in self.latest_response.json(),
            'has_keys': lambda v: all(key in self.latest_response.json() for key in v),
            'is_empty': lambda v: len(self.latest_response.text) == 0 if v else len(self.latest_response.text) > 0,
            'is_null': lambda v: self.latest_response.text == 'null' if v else self.latest_response.text != 'null'
        }
        
        return all(
            condition_checks.get(condition, lambda v: False)(value) 
            for condition, value in conditions.items()
        )
