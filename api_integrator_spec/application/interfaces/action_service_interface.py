from abc import ABC, abstractmethod

class ActionServiceInterface(ABC):
    @abstractmethod
    def perform_action(self, action_id, values):
        pass
