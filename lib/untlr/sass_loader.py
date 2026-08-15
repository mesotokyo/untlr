"""compile .scss file and include as CSS"""
from typing import Any
import sys
import tomllib
import logging
import subprocess
import re
from pathlib import Path

logger = logging.getLogger(__name__)

def compile_sass(config: dict[str, Any], file_path: str) -> str:
    sys_conf = config.get("system", {})
    cmd: str | None = sys_conf.get("sass_command", None)
    if cmd is None:
        logger.error("sass_command not found")
        return f"<!-- failed to render {file_path} -->"
    cwd: str | None = sys_conf.get("sass_cwd", None)
    
    args = re.split(r"\s+", cmd)
    args.append(file_path)

    # check file_path
    p = Path(file_path)
    if not p.exists():
        return f"""<!-- sass_loader: "{file_path}" not exists! -->"""
    
    logger.debug(f"args: {args}")
    logger.debug(f"cwd: {cwd}")
    try:
        proc = subprocess.run(args, shell=True, cwd=cwd, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(e)
        return f"<!-- failed to render {file_path} -->"
    return proc.stdout.decode("utf-8")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    try:
        with open("config.toml", "rb") as fp:
            config = tomllib.load(fp)
    except IOError:
        logger.critical("no config file given")
        sys.exit(-1)

    target = sys.argv[1]
    result = compile_sass(config, target)
    print(result)
