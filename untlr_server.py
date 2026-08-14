import os
import sys
import tomllib
import http
import argparse
from pathlib import Path
import logging

sys.path.append(os.path.abspath("lib"))
sys.path.append(os.path.abspath(os.path.join("depends", "jinja-importprops", "src")))
sys.path.append(os.path.abspath(os.path.join("depends", "npf-renderer", "src")))

from untlr.server import TestServer
                
logger = logging.getLogger("untlr_server")

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="render theme file")
    parser.add_argument("theme_file", metavar="THEME_FILE")
    parser.add_argument("-c", "--config",
                        metavar="CONFIG_FILE",
                        type=Path,
                        default=Path("config.toml"),
                        help="config file")
    parser.add_argument("--debug",
                        action="store_true")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    
    # load config file
    with open(args.config, "rb") as fp:
        TestServer.config = tomllib.load(fp)
    TestServer.config["theme_file"] = args.theme_file

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    listen = (TestServer.config["system"]["listen"], TestServer.config["system"]["port"])
    httpd = http.server.HTTPServer(listen, TestServer)
    logger.info(f"start server on {listen}")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
