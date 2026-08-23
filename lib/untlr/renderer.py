import sys
import os.path

from typing import Any
import json
import urllib.parse
import logging
from pathlib import Path

from jinja2 import Environment, DictLoader, FileSystemLoader
from jinja_importprops import ImportPropsExtension

from .tumblr_theme_parser import TumblrThemeParser
from .sass_loader import compile_sass

logger = logging.getLogger(__name__)

_templates = { "index": "" }
_jinja_env = Environment(
    loader = DictLoader(_templates),
    extensions = [ImportPropsExtension],
)

def _localize_func(text: str) -> str:
    return text

def _transform_func(fmt: str, text: str) -> str:
    if fmt == "Plaintext":
        return text
    if fmt == "JS":
        return text
    if fmt == "JSPlainText":
        return text
    if fmt == "URLEncoded":
        # text may be None or Undefined, so needs checking.
        if len(text) == 0:
            return ""
        return urllib.parse.quote(text)
    if fmt == "RGB":
        default = "0, 0, 0"
        if len(text) != 7:
            return default
        t = text.upper()
        try:
            rgb = [str(int(x, 16)) for x in (t[1:3], t[3:5], t[5:7])]
        except ValueError:
            return default
        return ", ".join(rgb)
    return ""

def _proc_arguments_func(name: str, value: str, args: list[str]) -> str:
    # parse args
    param: dict[str, str] = {}
    for a in args:
        k, v = a.split("=", 1)
        param[k] = v.strip("'" + '"')
    if name in ("ReblogButton", "LikeButton"):
        param["size"] = param.get("size", "24")
        param["color"] = param.get("color", "black")
        return value.format_map(param)
    return value

def pre_render(config: dict[str, Any]) -> str:
    template = ""
    base_dir = Path(".")
    if "theme_file" in config:
        with open(config["theme_file"], "rt", encoding="utf8") as fp:
            template = fp.read()
    elif "theme_dir" in config:
        base_dir = Path(config["theme_dir"])
        pre_env = Environment(
            loader = FileSystemLoader(config["theme_dir"]),
        )
        tmpl = pre_env.get_template("index.html")
        args = {
            "include_sass": lambda x:compile_sass(config, (base_dir / x))
        }
        template = tmpl.render(**args)
    return template

def render(config: dict[str, Any], vars: dict[str, Any] = {}) -> str:
    # 1. convert template to Jinja format
    template = pre_render(config)
    logger.debug(template)
    
    parser = TumblrThemeParser()
    parser.convert(template)
    parser.insert_partials()

    # 2. set Jinja format template and create object
    tmpl = parser.get_result()
    #logger.debug(tmpl)

    # 2.1. inject some code to template
    #tmpl = tmpl.replace("<head>", "<head>{{ _head_prepend_ }}")
    #_templates["index"] = tmpl
    #template = _jinja_env.get_template("index")
    template = _jinja_env.from_string(tmpl)

    # 3. prepare variables
    custom_vars = parser.get_custom_vars()

    tmpl_args: dict[str, Any] = {}
    tmpl_args.update(custom_vars)
    tmpl_args.update(vars)
    logger.debug(json.dumps(tmpl_args, indent=2, ensure_ascii=False))

    # 4. add some utility funcs
    tmpl_args["localize"] = _localize_func
    tmpl_args["transform"] = _transform_func
    tmpl_args["proc_arguments"] = _proc_arguments_func

    html = template.render(**tmpl_args)
    return html

