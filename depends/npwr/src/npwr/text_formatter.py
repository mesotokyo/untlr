from typing import TypedDict, ClassVar, Protocol
from collections.abc import Callable
import logging

from intervaltree import IntervalTree
logger = logging.getLogger(__name__)

from .npf_types import *
from .container_builder import ContainerBuilder, Node
from .util import get_handler

type TextFormatHandler = Callable[[TextFormatting], Node]

class RenderNode(TypedDict):
    start: int
    end: int
    type: str | list[str]

class TextFormatter:
    cm: ContainerBuilder
    tag_mapping: ClassVar[dict[str, tuple[str, str, dict[str, str]]]] = {
        # example: type: (<tag_name>, <class_name>, <attributes>)
        "bold": ("strong", "", {}),
        "italic": ("i", "", {}),
        "strikethrough": ("strike", "", {}),
        "small": ("small", "", {}),
    }

    def __init__(self, cm: ContainerBuilder):
        self.cm = cm

    def _create_node_common(self, fmt: TextFormatting) -> Node:
        logger.info(f"text create node ({fmt["type"]})...")
        if fmt["type"] == "link":
            return self.create_node_link(fmt)
        try:
            name, class_name, attr = self.tag_mapping[fmt["type"]]
        except KeyError:
            return self.cm.get_container()
        return self.cm.create_element(name, class_name, **attr)

    def create_node_link(self, fmt: TextFormatting) -> Node:
        if not "url" in fmt:
            return self.cm.get_col_container()
        href = fmt["url"]
        return self.cm.create_element("a", href=href)

    def create_node_text(self, fmt: TextFormatting) -> Node:
        return self._create_node_common(fmt)

    def create_node_bold(self, fmt: TextFormatting) -> Node:
        return self._create_node_common(fmt)

    def create_node_italic(self, fmt: TextFormatting) -> Node:
        return self._create_node_common(fmt)

    def create_node_strikethrough(self, fmt: TextFormatting) -> Node:
        return self._create_node_common(fmt)

    def create_node_small(self, fmt: TextFormatting) -> Node:
        return self._create_node_common(fmt)
    
    def _get_container(self, fmt: TextFormatting) -> Node:
        fallback: TextFormatHandler = lambda x: self.cm.get_container()
        handler = get_handler(self, "create_node", fmt["type"], fallback)
        return handler(fmt)

    def _create_tree(self, formatting: list[TextFormatting], text: str) -> IntervalTree:
        result = IntervalTree()
        for fmt in formatting:
            result[fmt["start"]:fmt["end"]] = fmt
        # add text node
        tnode: RenderNode = {
            "start": 0,
            "end": len(text),
            "type": "text"
        }
        result[0:len(text)] = tnode
        # split and merge tree
        def merger(current_data: TextFormatting | list[TextFormatting], new_data):
            if not isinstance(current_data, list):
                current_data = [current_data]
            current_data.append(new_data)
            return current_data

        result.split_overlaps()
        result.merge_overlaps(merger)
        return result
    
    def format(self, formatting: list[TextFormatting], text: str) -> list[Node]:
        if len(formatting) == 0:
            c = self.cm.get_container()
            c["children"].append(text)
            return [c]

        nodes: list[Node] = []

        for tree_node in sorted(self._create_tree(formatting, text)):
            # temporary create text node
            t_fmt: TextFormatting = {
                "start": tree_node.begin,
                "end": tree_node.end,
                "type": "text"
            }
            text_node = self._create_node_common(t_fmt)
            text_node["children"].append(text[tree_node.begin:tree_node.end])
            
            if not isinstance(tree_node.data, list):
                fmt: TextFormatting = tree_node.data
                n = self._create_node_common(fmt)
                n["children"].append(text_node)
                nodes.append(n)
                continue
                
            if isinstance(tree_node.data, list):
                last_node = text_node
                fmts: list[TextFormatting]  = tree_node.data
                for fmt in fmts:
                    if fmt["type"] == "text":
                        continue
                    n = self._create_node_common(fmt)
                    n["children"].append(last_node)
                    last_node = n
                nodes.append(last_node)
                    
        return nodes
