from typing import ClassVar, Any
import http.server
import tomllib
import logging
import json
from http import HTTPStatus
from wsgiref.types import WSGIEnvironment, StartResponse
import time
import email.utils

from .renderer import render
from .variable_manager import VariableManager

logger = logging.getLogger(__name__)

class ServerApp:
    config: ClassVar[dict[str, Any]] = {}
    environ: WSGIEnvironment
    start_response: StartResponse

    def __init__(self, environ: WSGIEnvironment, start_response: StartResponse):
        self.environ = environ
        self.start_response = start_response

    def date_time_string(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        return email.utils.formatdate(timestamp, usegmt=True)
        
    def send(self, status:HTTPStatus, content: str = "") -> bytes:
        if content:
            resp = content.encode("utf-8")
        else:
            resp = f"{status.phrase}".encode("utf-8")
        response_headers = [
            ('Content-type', 'text/html'),
            ("Content-Length", str(len(resp))),
            ("Last-Modified", self.date_time_string())            
        ]
        self.start_response(f"{status.value} {status.phrase}", response_headers)
        return resp

    def __iter__(self):
        method = self.environ["REQUEST_METHOD"]
        path = self.environ["PATH_INFO"]

        if method != "GET":
            yield self.send(HTTPStatus(404))
            return
        
        vm = VariableManager(self.config)
        vars = vm.generate_for_path(path)
        if "Posts" in vars:
            logger.debug(json.dumps(vars["Posts"][0], indent=2, ensure_ascii=False))

        html = render(self.config, vars).encode("utf-8")

        status = '200 OK'
        response_headers = [
            ('Content-type', 'text/html'),
            ("Content-Length", str(len(html))),
            ("Last-Modified", self.date_time_string())            
        ]
        self.start_response(status, response_headers)
        yield html

class TestServer(http.server.BaseHTTPRequestHandler):
    config: ClassVar[dict[str, Any]] = {}
    
    def do_GET(self):
        """Serve a GET request."""

        # if self.path != "/":
        #     self.send_response(404)
        #     self.end_headers()
        #     return

        vm = VariableManager(self.config)
        vars = vm.generate_for_path(self.path)
        if "Posts" in vars:
            logger.debug(json.dumps(vars["Posts"][0], indent=2, ensure_ascii=False))

        html = render(self.config, vars).encode("utf-8")
        self.send_response(200)
        self.send_header("Context-Type", "text/html")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Last-Modified", self.date_time_string())
        self.end_headers()
        self.wfile.write(html)

    

