import yaml
import json
from pathlib import Path
from src.domain.interfaces.oas_parser_interface import OasParserInterface
from src.domain.entities.api_specification import ApiSpecification
from src.domain.exceptions.oas_parser_exception import OasParserException
from src.domain.value_objects.yml_obj import YmlObj

class AbstractOasParser(OasParserInterface):
    def __init__(self):
        self.data = YmlObj({})

    def load_data(self, oas_file_path: str) -> None:
        try:
            path = Path(oas_file_path)
            content = path.read_text()

            if path.suffix == '.json':
                self.data = YmlObj(json.loads(content))
            elif path.suffix in ['.yaml', '.yml']:
                self.data = YmlObj(yaml.safe_load(content))
            else:
                raise OasParserException(f"Unsupported file format: {path.suffix}")

            if not self.data:
                raise OasParserException(f"Failed to parse file content as {path.suffix.upper()}")

            if 'openapi' not in self.data:
                raise OasParserException("Invalid OpenAPI specification: 'openapi' version not found.")
        except json.JSONDecodeError as e:
            raise OasParserException(f"Failed to parse JSON: {str(e)}")
        except yaml.YAMLError as e:
            raise OasParserException(f"Failed to parse YAML: {str(e)}")
        except Exception as e:
            raise OasParserException(f"Error loading OAS file: {str(e)}")

    @staticmethod
    def generate_operation_id(method: str, path: str) -> str:
        parts = [part for part in path.lstrip('/').split('/') if not part.startswith('{')]
        operation_id = method.lower() + ''.join(part.capitalize() for part in parts)
        return operation_id[0].lower() + operation_id[1:]
