from typing import ClassVar, Any
import http.server
import tomllib
import logging
import json

from .renderer import render
from .variable_manager import VariableManager

logger = logging.getLogger(__name__)

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

        with open(self.config["theme_file"], "rt", encoding="utf8") as fp:
            tmpl = fp.read()
            logger.debug(json.dumps(vars["Posts"][0], indent=2, ensure_ascii=False))

        html = render(tmpl, vars).encode("utf-8")
        self.send_response(200)
        self.send_header("Context-Type", "text/html")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Last-Modified", self.date_time_string())
        self.end_headers()
        self.wfile.write(html)

    

