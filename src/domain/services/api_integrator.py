import json
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, List, Union, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

import requests
import aiohttp
import asyncio
from flask import Flask, jsonify
from snoop import snoop
import pykwalify.core

from src.domain.value_objects.api_response import ApiResponse
from src.domain.value_objects.obj_utils import Obj

class ApiIntegrator:
  def __init__(self, config_path: str, max_workers: int = 10, schema_path: str = None):
    config_path = Path(__file__).resolve().parent.parent.parent / config_path
    
    # Default schema path if not provided
    if schema_path is None:
      schema_path = Path(__file__).resolve().parent.parent.parent / 'infrastructure' / 'schemas' / 'api_integrator_schema.yml'
    
    # Validate configuration against schema
    try:
      pykwalify.core.Core(source_file=config_path, schema_files=[schema_path]).validate()
    except Exception as e:
      logging.error(f"Configuration validation failed: {e}")
      raise ValueError(f"Invalid configuration: {e}")

    self.config = Obj.from_yaml(config_path)
    self.vars = self.config.vars if self.config.has('vars') else Obj({})
    self.constants = self.config.constants if self.config.has('constants') else Obj({})
    self.session = requests.Session()
    self.latest_response = None
    self._setup_logging()
    self.action_number = 0
    self.action_depth = 0  # Track recursion depth
    self.app = None
    self.max_workers = max_workers
    
    # Check if we should run as server
    if self.config.get('as_server', False):
        self.app = Flask(__name__)
        self._setup_endpoints()
    
    # Initialize my_app_server
    self.vars['my_app_server'] = self.config.my_app_server if self.config.has(
      'my_app_server') else 'http://localhost:8000'

  # ... [rest of the file remains the same] ...
