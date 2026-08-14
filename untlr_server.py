import os
import sys
import tomllib
import http

sys.path.append(os.path.abspath("lib"))
sys.path.append(os.path.abspath(os.path.join("depends", "jinja-importprops", "src")))
sys.path.append(os.path.abspath(os.path.join("depends", "npf-renderer", "src")))


from untlr.server import TestServer
                
_CONFIG_FILE = "config.toml"

if __name__ == "__main__":
    # load config file
    with open(_CONFIG_FILE, "rb") as fp:
        TestServer.config = tomllib.load(fp)

    listen = (TestServer.config["system"]["listen"], TestServer.config["system"]["port"])
    httpd = http.server.HTTPServer(listen, TestServer)
    print(f"start server on {listen}")
    httpd.serve_forever()
