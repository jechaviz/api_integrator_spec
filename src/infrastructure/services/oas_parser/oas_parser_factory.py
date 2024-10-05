import yaml
import json
from pathlib import Path
from src.domain.interfaces.oas_parser_interface import OasParserInterface
from src.domain.exceptions.oas_parser_exception import OasParserException
from src.infrastructure.services.oas_parser.oas30_parser import Oas30Parser
from src.infrastructure.services.oas_parser.oas31_parser import Oas31Parser

class OasParserFactory:
    @staticmethod
    def create(file_path: str) -> OasParserInterface:
        path = Path(file_path)
        if not path.exists():
            raise OasParserException(f"File not found: {file_path}")

        try:
            content = path.read_text()
            data = OasParserFactory._parse_content(content, path.suffix)
            return OasParserFactory._create_parser_by_version(data)
        except Exception as e:
            raise OasParserException(f"Error creating OAS parser: {str(e)}")

    @staticmethod
    def _parse_content(content: str, extension: str) -> dict:
        if extension == '.json':
            data = json.loads(content)
        elif extension in ['.yaml', '.yml']:
            data = yaml.safe_load(content)
        else:
            raise OasParserException(f"Unsupported file format: {extension}")

        if not isinstance(data, dict):
            raise OasParserException("Invalid OpenAPI specification: file content is not a valid JSON/YAML.")

        if 'openapi' not in data or not isinstance(data['openapi'], str):
            raise OasParserException("Invalid OpenAPI specification: 'openapi' version not found or invalid.")

        return data

    @staticmethod
    def _create_parser_by_version(data: dict) -> OasParserInterface:
        version = data['openapi']
        if version.startswith('3.0'):
            return Oas30Parser()
        elif version.startswith('3.1'):
            return Oas31Parser()
        else:
            raise OasParserException(f"Unsupported OpenAPI version: {version}")
