#!/usr/bin/env python3
import json
import sys
from enum import auto, IntFlag
from typing import TypedDict

import logging
logger = logging.getLogger(__name__)

from .container_builder import ContainerBuilder, Node, NodeList
from .npf_types import *
from .block_renderer import BlockRenderer, StackOperation
from .html_renderer import render_html

class RendererOption(IntFlag):
    NONE = 0
    SKIP_TITLE = auto()
    TRUNCATE = auto()

class RendererConfig(TypedDict):
    option: RendererOption

class ContainerStack:
    stack: list[Node]
    def __init__(self):
        self.stack = []

    def push(self, containers: list[Node]):
        self.stack.extend(containers)

    def pop(self, count: int = 1) -> Node:
        if count < 1:
            raise IndexError(f"count must be larger than 1")
        for _ in range(count):
            ret = self.stack.pop()
            try:
                c = self.current()
            except IndexError:
                return ret
            c["children"].append(ret)
        return ret

    def current(self) -> Node:
        return self.stack[-1]

    def operate(self, ops: list[StackOperation]):
        for op in ops:
            if "pop_nodes" in op:
                self.pop(op["pop_nodes"])
            if "push_nodes" in op:
                self.push(op["push_nodes"])

class RenderState(TypedDict):
    previous_block: ContentBlock | None
    node_stack: ContainerStack

class NPFWebRenderer:
    config: RendererConfig
    _cb: ContainerBuilder
    _rdr: BlockRenderer
    _state: RenderState

    def __init__(self, config: RendererConfig):
        self.config = config
        self._cb = ContainerBuilder()
        self._rdr = BlockRenderer(self._cb)
        self._state = { "previous_block": None, "node_stack": ContainerStack() }

    def _create_default_layout(self, content: list[ContentBlock]) -> list[Layout]:
        block_count = len(content)
        display: list[RowLayout] = [{ "blocks": [x] } for x in range(0, block_count)]
        result: list[Layout] = [
            {
                "type": "rows",
                "display": display,
            }
        ]
        return result

    def _push_container_stack(self, containers: list[Node]):
            self._state["node_stack"].push(containers)

    def _pop_container_stack(self, count: int = 1) -> Node:
        return self._state["node_stack"].pop(count)

    def _current_container(self) -> Node:
        return self._state["node_stack"].current()
            
    def _enter_and_exit_handler(self, block: ContentBlock | None):
        prev_block = self._state["previous_block"]
        self._state["previous_block"] = block
        ops = self._rdr.enter(prev_block, block)
        self._state["node_stack"].operate(ops)

    def _render_layout(self, content: list[ContentBlock],
                   layout: Layout) -> Node | NodeList:
        if layout["type"] != "rows":
            msg = f"`{layout["type"]}` layout is currently not supported"
            raise LayoutNotSupportedError(msg)

        # check if truncate `truncate_after` or not
        if self.config["option"] & RendererOption.TRUNCATE:
            truncate = layout.get("truncate_after", None)
        else:
            truncate = None

        self._push_container_stack([self._cb.get_container()])
        for raw_layout in layout["display"]:
            # `blocks` contains pair of content and block index
            blocks = [(content[x], x) for x in raw_layout["blocks"]]
            for block, index in blocks:
                # if block index is bigger than `truncate_after`, skip process
                if truncate is not None and index > truncate:
                    continue
                self._enter_and_exit_handler(block)
                node = self._render_block(block, index)
                if node is not None:
                    self._current_container()["children"].append(node)
        self._enter_and_exit_handler(None)
        return self._pop_container_stack()

    def _render_block(self, block: ContentBlock, index: int) -> Node | None:
        self._enter_and_exit_handler(block)
        
        if is_text_block(block):
            if (self.config["option"] & RendererOption.SKIP_TITLE
                and index == 0
                and block.get("subtype", "") == "heading1"):
                return None
            return self._rdr.render_text(block, index)
        if is_image_block(block):
            return self._rdr.render_image(block, index)
        logger.info(f"""renderer for `{block["type"]}` type is not implemented""")
        return self._cb.get_container()

    def render(self, npf: NPFDict) -> str:
        try:
            content = npf["content"]
        except KeyError:
            raise ContentNotExistsError("`content` block does not exist")
            
        layouts = npf.get("layout") or self._create_default_layout(content)
        nodes: list[Node | NodeList] = []
        for layout in layouts:
            nodes.append(self._render_layout(content, layout))

        result: list[str] = []
        for node in nodes:
            if isinstance(node, list):
                for sub_node in node:
                    result.append(render_html(sub_node))
            else:
                result.append(render_html(node))
        return "".join(result)
    
if __name__ == "__main__":
    config: RendererConfig = { "option": RendererOption.NONE }
    renderer = NPFWebRenderer(config)

    content = sys.stdin.read()
    npf = json.loads(content)
    result = renderer.render(npf)
    print(result)
