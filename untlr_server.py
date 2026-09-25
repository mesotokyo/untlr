import re
import os
import sys
import tomllib
import http.server
import argparse
from pathlib import Path
import logging
from typing import Any
from wsgiref.simple_server import make_server

sys.path.append(os.path.abspath("lib"))
sys.path.append(os.path.abspath(os.path.join("depends", "jinja-importprops", "src")))
sys.path.append(os.path.abspath(os.path.join("depends", "npwr", "src")))
sys.path.append(os.path.abspath(os.path.join("depends", "tyconf", "src")))

import livereload
from tyconf import TomlWriter
from tyconf.tyconf import ParseError
from untlr.server import ServerApp
from untlr.renderer import pre_render
from untlr.config import UntlrConfig

logger = logging.getLogger("untlr_server")

"""create custom livereload.Server class to suppress redundant log message"""
class CustomLiveReloadServer(livereload.Server):
    def _setup_logging(self):
        pass

class Arguments(argparse.Namespace):
    theme_file: Path | None
    config: Path
    debug: bool
    config_skelton: bool

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
    parser.add_argument("--render",
                        metavar="OUTPUT_FILE",
                        type=Path,
                        default=None)
    parser.add_argument("--config-skelton",
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
    server = CustomLiveReloadServer(ServerApp)
    if "theme_file" in config:
        server.watch(config["theme_file"])
    if "theme_dir" in config:
        server.watch(config["theme_dir"], ignore=lambda x:check_excluded(x, ignore_re))
    host = config["system"]["listen"]
    port = config["system"]["port"]
    server.serve(port=port, host=host)

def start_server(config: dict[str, Any]):
    ServerApp.config.update(config)
    listen = config["system"]["listen"]
    port = config["system"]["port"]
    logger.info(f"start server on {listen}:{port}")
    with make_server(listen, port, ServerApp) as httpd:
        httpd.serve_forever()

def render(config: dict[str, Any], output_path):
    with output_path.open("wt", encoding="utf-8") as fp:
        output = pre_render(config)
        fp.write(output)

def main():
    parser = get_parser()
    args = parser.parse_args(namespace=Arguments())
    config = UntlrConfig()

    if args.config_skelton:
        writer = TomlWriter()
        writer.dump(sys.stdout, config)
        sys.exit(0)
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # load config file
    try:
        config.parse_file(str(args.config))
    except ParseError:
        msg = "Config file is not found. \nYou can generate it by `untlr_server.py --config-skelton > config.toml` command."
        print(msg, file=sys.stderr)
        sys.exit(-1)

    if not args.debug:
        try:
            log_level = config["system"]["log_level"]
        except KeyError:
            log_level = "INFO"
        try:
            llv = logging.getLevelNamesMapping()[log_level.upper()]
        except KeyError:
            print(f"invalid log level: {log_level}", file=sys.stderr)
            sys.exit(-1)
        logging.basicConfig(level=llv)

    if args.theme_file:
        if args.theme_file.is_file():
            config["theme_file"] = args.theme_file
        if args.theme_file.is_dir():
            config["theme_dir"] = args.theme_file

    if (not "theme_file" in config
        and not "theme_dir" in config):
        logger.critical("theme file or directory not given, or invalid file or directory is given")
        sys.exit(-1)

    if args.render:
        render(config, args.render)
        sys.exit(0)
        
    if config.get("watch", {}).get("enabled", False):
        start_live_server(config)
    else:
        start_server(config)
        

if __name__ == "__main__":
    main()
