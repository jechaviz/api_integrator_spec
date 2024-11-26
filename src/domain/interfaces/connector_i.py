from abc import ABC, abstractmethod
from typing import Any, Dict

class ConnectorI(ABC):
    """Interface that all connectors must implement"""
    
    @abstractmethod
    def execute(self, command: str, data: Any, params: Dict) -> Any:
        """
        Execute the connector's command
        
        Args:
            command: The command to execute (e.g. 'http.get', 'vars.set')
            data: The data needed for the command
            params: Additional parameters and context
            
        Returns:
            Any: The result of the command execution
        """
        pass
