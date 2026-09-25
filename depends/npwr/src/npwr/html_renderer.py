import html
from typing import Any, TypedDict
import logging
logger = logging.getLogger(__name__)

from .container_builder import Node, NodeList, HtmlElement

VOID_ELEMENTS = set(("area", "base", "br", "col", "embed", "hr",
                     "img", "input", "link", "meta", "param", "source", "track", "wbr"))

def render_html(node: Node | NodeList) -> str:
    return render_nodes(node)

def render_nodes(node: Node | NodeList | str) -> str:
    if isinstance(node, list):
        results = [_render_node(x) for x in node]
        return "".join(results)
    return _render_node(node)

def _render_node(node: Node | str) -> str:
    if isinstance(node, str):
        return html.escape(node)
    if not "tag_name" in node:
        return render_nodes(node["children"])
    return _render_html_tag(node)
        
def _render_html_tag(node: HtmlElement) -> str:
    results: list[str] = []
    results.append(_start_tag(node))
    results.append(render_nodes(node["children"]))
    results.append(_end_tag(node))
    return "".join(results)
    
def _start_tag(node: HtmlElement) -> str:
    attrs: list[str] = []
    for k, v in node["attributes"]:
        quot = '"'
        if v.find(quot) >= 0:
            quot = "'"
        if v is not None:
            attrs.append(f"""{k}={quot}{v}{quot}""")
        else:
            attrs.append(k)
    att = " ".join(attrs)
    if att:
        att = " " + att
    return f"""<{node["tag_name"]}{att}>"""

def _end_tag(node: HtmlElement) -> str:
    if node["tag_name"] in VOID_ELEMENTS:
        return ""
    return f"""</{node["tag_name"]}>"""
