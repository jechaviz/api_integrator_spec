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

from src.domain.value_objects.api_response import ApiResponse
from src.domain.value_objects.obj_utils import Obj

class ApiIntegrator:
  def __init__(self, config_path: str, max_workers: int = 10):
    config_path = Path(__file__).resolve().parent.parent.parent / config_path
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

  # ... [previous methods remain the same] ...

  async def _async_http_request(self, method: str, url: str, headers: dict = None, 
                                 data: str = None, params: dict = None) -> ApiResponse:
    """Async HTTP request method using aiohttp"""
    async with aiohttp.ClientSession() as session:
      logging.info(f'Async Request: 🔹{method}🔹 {url} {headers} {params} {data}')
      async with session.request(method, url, headers=headers, data=data, params=params) as response:
        body = await response.text()
        response_obj = requests.Response()
        response_obj.status_code = response.status
        response_obj.url = str(response.url)
        response_obj.headers = dict(response.headers)
        response_obj._content = body.encode('utf-8')
        api_response = ApiResponse(response_obj)
        logging.info(f'Async Response [{response.status}] {body[:200]}')
        return api_response

  def _threaded_bulk_request(self, method: str, url: str, items: List[Any], 
                              headers: dict = None, wrapper: str = '') -> List[ApiResponse]:
    """Perform bulk requests using ThreadPoolExecutor"""
    def single_request(item):
      wrapped_item = {wrapper: item} if wrapper else item
      body = json.dumps(wrapped_item)
      headers_copy = headers.copy() if headers else {}
      headers_copy['Content-Type'] = 'application/json'
      
      response = self.session.request(method, url, headers=headers_copy, data=body)
      return ApiResponse(response)

    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
      futures = [executor.submit(single_request, item) for item in items]
      return [future.result() for future in as_completed(futures)]

  async def _async_bulk_request(self, method: str, url: str, items: List[Any], 
                                 headers: dict = None, wrapper: str = '') -> List[ApiResponse]:
    """Async bulk request method"""
    async def single_request(item):
      wrapped_item = {wrapper: item} if wrapper else item
      body = json.dumps(wrapped_item)
      headers_copy = headers.copy() if headers else {}
      headers_copy['Content-Type'] = 'application/json'
      
      async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers_copy, data=body) as response:
          body_text = await response.text()
          response_obj = requests.Response()
          response_obj.status_code = response.status
          response_obj.url = str(response.url)
          response_obj.headers = dict(response.headers)
          response_obj._content = body_text.encode('utf-8')
          return ApiResponse(response_obj)

    tasks = [single_request(item) for item in items]
    return await asyncio.gather(*tasks)

  def _handle_http(self, command: str, data: Obj, params: Obj):
    method = command.split('.')[1].upper()
    endpoint = data.get('path', '') or data.get('url', '')
    url = self.render_template(endpoint, params)
    headers = Obj({k: self.render_template(v, params) for k, v in data.get('headers', Obj({})).items()})
    body_data = data.get('body', Obj({}))
    query = Obj({k: self.render_template(v, params) for k, v in data.get('query', Obj({})).items()})

    # Remove None values from query parameters
    query_dict = {k: v for k, v in query.to_dict().items() if v is not None}
    headers_dict = headers.to_dict()

    # Check for async or threaded bulk request
    if data.get('type') == 'bulk':
      wrapper = data.get('wrapper', '')
      items = self.render_template(body_data, params)
      
      # Prefer async if available, fallback to threading
      if data.get('async', False):
        try:
          responses = asyncio.run(self._async_bulk_request(method, url, items, headers_dict, wrapper))
        except Exception as e:
          logging.error(f"Async bulk request failed: {e}")
          responses = self._threaded_bulk_request(method, url, items, headers_dict, wrapper)
      else:
        responses = self._threaded_bulk_request(method, url, items, headers_dict, wrapper)
      
      # Store responses in vars for further processing
      self.vars['bulk_responses'] = responses
      self.latest_response = responses[-1] if responses else None
    else:
      # Standard single request
      body = self.render_template(json.dumps(body_data.to_dict()), params)
      
      # Check for async request
      if data.get('async', False):
        try:
          response = asyncio.run(self._async_http_request(method, url, headers_dict, body, query_dict))
        except Exception as e:
          logging.error(f"Async request failed: {e}")
          response = self.session.request(method, url, headers=headers_dict, data=body, params=query_dict)
          response = ApiResponse(response)
      else:
        response = self.session.request(method, url, headers=headers_dict, data=body, params=query_dict)
        response = ApiResponse(response)
      
      params['response'] = response
      self.latest_response = response
      self.vars['response'] = response

# ... [rest of the file remains the same] ...
