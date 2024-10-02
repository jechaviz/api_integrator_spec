from abc import ABC, abstractmethod

class ApiParserInterface(ABC):
    @abstractmethod
    def action_requests(self, action_id, values):
        pass
