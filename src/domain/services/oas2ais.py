import logging
from pathlib import Path
from typing import Dict, List, Any

import yaml

from src.domain.value_objects.obj_utils import Obj

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAPIToAPIIntegratorSpecificationMapper:
  def __init__(self, openapi_file: str):
    self.openapi_data = self._load_openapi_data(openapi_file)
    self.configuration = Obj({
      "api_integrator": "1.0.0",
      "info": {},
      "supplier_servers": [],
      "actions": {},
      "tags": [],
      "my_app_server": {}
    })
    self.openapi_version = self._detect_oas_version()

  def _load_openapi_data(self, file_path: str) -> Obj:
    """Load OpenAPI data from a YAML file."""
    with open(file_path, 'r') as f:
      return Obj(yaml.safe_load(f))

  def _detect_oas_version(self) -> str:
    """Determine OpenAPI version for flexible mapping."""
    version = self.openapi_data.openapi or ""
    if version.startswith("3.1"):
      return "3.1"
    elif version.startswith("3.0"):
      return "3.0"
    else:
      raise ValueError("Unsupported OpenAPI version. Only 3.0 and 3.1 are supported.")

  def map_info(self) -> None:
    """Map OpenAPI info to configuration."""
    info = self.openapi_data.info or Obj({})
    self.configuration.info = {
      "title": info.title or "",
      "version": info.version or "",
      "description": info.description or "",
      "contact": info.contact or {}
    }

  def map_servers(self) -> None:
    """Map servers from OpenAPI to configuration."""
    servers = self.openapi_data.servers or []
    for index, server in enumerate(servers):
      self.configuration.supplier_servers.append({
        "id": f"server-{index + 1}",
        "url": server.url or "",
        "description": server.description or ""
      })

  def map_tags(self) -> None:
    """Map tags from OpenAPI to configuration."""
    tags = self.openapi_data.tags or []
    self.configuration.tags = [{"name": tag.name, "description": tag.description or ""} for tag in tags]

  def map_actions(self) -> None:
    """Map actions from OpenAPI paths to configuration."""
    paths = self.openapi_data.paths or Obj({})
    for path, path_data in paths.items():
      for method, method_data in path_data.items():
        action_name = method_data.operationId if method_data.has('operationId') else f"{method}_{path}"
        action = {
          "name": action_name,
          "tags": method_data.tags or [],
          "description": method_data.summary or "",
          "performs": self._extract_performs(method_data)
        }

        if self.openapi_version == "3.1":
          action["jsonSchema"] = self._extract_json_schema(method_data)

        self.configuration.actions[action_name] = action

  def _extract_performs(self, method_data: Obj) -> List[Dict[str, Any]]:
    """Extract performs from method data."""
    responses = method_data.responses or Obj({})
    performs = []
    for status, response in responses.items():
      perform_entry = {"action": f"status_{status}", "responses": []}

      if response.has("content"):
        content_type, content_data = next(iter(response.content.items()), (None, None))
        perform_entry["data"] = {
          "type": content_type or "application/json",
          "schema": self._get_schema(content_data)
        }

      performs.append(perform_entry)
    return performs

  def _get_schema(self, content_data: Obj) -> Dict[str, Any]:
    """Extract schema from content data."""
    if content_data and content_data.has("schema"):
      return content_data.schema
    return {}

  def _extract_json_schema(self, method_data: Obj) -> Dict[str, Any]:
    """Extract JSON schema from method data for OpenAPI 3.1."""
    if method_data.has("requestBody.content"):
      content_type, content_data = next(iter(method_data.requestBody.content.items()), (None, None))
      if content_data and content_data.has("schema"):
        return content_data.schema
    return {}

  def save_configuration(self, output_path: str) -> None:
    """Save the configuration to a YAML file."""
    self.configuration.save(output_path)
    logger.info(f"YAML configuration saved to {output_path}")


def main(openapi_file: str, output_yaml: str) -> None:
  """Main function to execute the mapping process."""
  mapper = OpenAPIToAPIIntegratorSpecificationMapper(openapi_file)
  mapper.map_info()
  mapper.map_servers()
  mapper.map_tags()
  mapper.map_actions()
  mapper.save_configuration(output_yaml)


if __name__ == "__main__":
  input_path = str(Path(__file__).parent.parent.parent / 'infrastructure/specs/oas/ctonline.yml')
  output_path = str(Path(__file__).parent.parent.parent / 'infrastructure/specs/api_integrator' / (
      Path(input_path).stem + '_ai.yaml'))
  main(input_path, output_path)
