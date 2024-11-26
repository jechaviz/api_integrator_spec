from typing import Any, Dict
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.domain.interfaces.connector_i import ConnectorI

class WebConnector(ConnectorI):
    def __init__(self, api_integrator):
        self.api = api_integrator
        self.driver = None
        
    def execute(self, command: str, data: Any, params: Dict) -> None:
        """Execute web automation commands"""
        action, selector_type = command.split('.')
        
        if not self.driver:
            self.driver = webdriver.Chrome()  # Or configured browser
            
        try:
            if action == 'fill':
                self._fill_element(selector_type, data, params)
            elif action == 'click':
                self._click_element(selector_type, data, params)
            elif action == 'select':
                self._select_option(selector_type, data, params)
        except Exception as e:
            logging.error(f"Web automation error: {e}")
            raise
            
    def _fill_element(self, selector_type: str, data: Any, params: Dict):
        element = self._find_element(selector_type, data['selector'])
        element.send_keys(data['value'])
        
    def _click_element(self, selector_type: str, data: Any, params: Dict):
        element = self._find_element(selector_type, data)
        element.click()
        
    def _select_option(self, selector_type: str, data: Any, params: Dict):
        element = self._find_element(selector_type, data['selector'])
        element.select_by_value(data['value'])
        
    def _find_element(self, selector_type: str, selector: str):
        by_type = {
            'css': By.CSS_SELECTOR,
            'xpath': By.XPATH,
            'id': By.ID,
            'name': By.NAME
        }.get(selector_type, By.CSS_SELECTOR)
        
        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((by_type, selector))
        )
