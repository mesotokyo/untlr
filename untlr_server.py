import re
import os
import sys
import tomllib
import http.server
import argparse
from pathlib import Path
import logging
from typing import Any

sys.path.append(os.path.abspath("lib"))
sys.path.append(os.path.abspath(os.path.join("depends", "jinja-importprops", "src")))
sys.path.append(os.path.abspath(os.path.join("depends", "npf-renderer", "src")))

from untlr.server import TestServer, ServerApp
import livereload
                
logger = logging.getLogger("untlr_server")

"""create custom livereload.Server class to suppress redundant log message"""
class CustomLiveReloadServer(livereload.Server):
    def _setup_logging(self):
        pass

class Arguments(argparse.Namespace):
    theme_file: Path | None
    config: Path
    debug: bool

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="render theme file")
    parser.add_argument("theme_file",
                        metavar="THEME_FILE",
                        type=Path,
                        nargs="?")
    parser.add_argument("-c", "--config",
                        metavar="CONFIG_FILE",
                        type=Path,
                        default=Path("config.toml"),
                        help="config file")
    parser.add_argument("--debug",
                        action="store_true")
    return parser

def check_excluded(filename: str, excludes: list[re.Pattern]) -> bool:
    basename = os.path.basename(filename)
    for p in excludes:
        if p.match(basename):
            return True
    return False

def start_live_server(config: dict[str, Any]):
    ignores: list[str] = config.get("watch", {}).get("ignore", [])
    ignore_re: list[re.Pattern] = []
    for t in ignores:
        ignore_re.append(re.compile(t))

    ServerApp.config.update(config)
    #server = livereload.Server(ServerApp)
    server = CustomLiveReloadServer(ServerApp)
    if "theme_file" in config:
        server.watch(config["theme_file"])
    if "theme_dir" in config:
        server.watch(config["theme_dir"], ignore=lambda x:check_excluded(x, ignore_re))
    host = config["system"]["listen"]
    port = config["system"]["port"]
    server.serve(port=port, host=host)

def start_server(config: dict[str, Any]):
    TestServer.config.update(config)
    listen = (config["system"]["listen"], config["system"]["port"])
    httpd = http.server.HTTPServer(listen, TestServer)
    logger.info(f"start server on {listen}")
    httpd.serve_forever()

def main():
    parser = get_parser()
    args = parser.parse_args(namespace=Arguments())
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # load config file
    try:
        with open(args.config, "rb") as fp:
            config = tomllib.load(fp)
    except IOError:
        logger.critical("no config file given")
        sys.exit(-1)

    if args.theme_file:
        if args.theme_file.is_file():
            config["theme_file"] = args.theme_file
        if args.theme_file.is_dir():
            config["theme_dir"] = args.theme_file

    if (not "theme_file" in config
        and not "theme_dir" in config):
        logger.critical("theme file or directory not given or invalid file or directory is given")
        sys.exit(-1)

    if config.get("watch", {}).get("enabled", False):
        start_live_server(config)
    else:
        start_server(config)
        

if __name__ == "__main__":
    main()
