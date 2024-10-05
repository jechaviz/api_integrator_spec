from abc import ABC, abstractmethod
from src.domain.entities.api_specification import ApiSpecification

class OasParserInterface(ABC):
    @abstractmethod
    def parse(self, oas_file_path: str = '') -> ApiSpecification:
        pass

    @abstractmethod
    def get_api_name(self) -> str:
        pass

    @abstractmethod
    def get_base_url(self) -> str:
        pass

    @abstractmethod
    def get_version(self) -> str:
        pass
