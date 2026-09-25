from typing import TypedDict, ClassVar, NotRequired, Iterator
from collections.abc import Callable
from operator import itemgetter
import logging
logger = logging.getLogger(__name__)

from .npf_types import *
from .container_builder import ContainerBuilder, Node
from .text_formatter import TextFormatter
from .util import get_handler

class StackOperation(TypedDict, total=False):
    push_nodes: list[Node]
    pop_nodes: int

type EnterExitHandler = Callable[[ContentBlock | None, ContentBlock | None], list[StackOperation]]
type RenderHandler = Callable[[ContentBlock, int], Node]

class BlockRenderer:
    """
    Implement rendering methods. This class must be stateless.
    In other Words, this class does not have property  that contains state, and
    state management should be handled by the layout management (renderer) class.

    This class implements methods for individual block types and subtypes
    to make the class expandable.
    """
    _cm: ContainerBuilder
    _tf: TextFormatter

    def __init__(self,
                 container_builder: ContainerBuilder | None = None,
                 text_formatter: TextFormatter | None = None):
        if container_builder is None:
            self._cm = ContainerBuilder()
        else:
            self._cm = container_builder
        if text_formatter is None:
            self._tf = TextFormatter(cm=self._cm)
        else:
            self._tf = text_formatter

    def _get_enter_handler(self, name: str) -> EnterExitHandler:
        return get_handler(self, "enter", name, lambda x,y: [])

    def _get_exit_handler(self, name: str) -> EnterExitHandler:
        return get_handler(self, "exit", name, lambda x,y: [])

    def _get_render_handler(self, prefix: str, name: str, fallback: str) -> RenderHandler:
        fb_func = getattr(self, fallback)
        return get_handler(self, prefix, name, fb_func)

    def _gen_get_handler[T](self, prefix: str, name: str, fallback: T) -> T:
        qn = name.replace("-", "_")
        fname = f"""{prefix}_{qn}"""
        try:
            func: T = getattr(self, fname)
        except AttributeError:
            msg = f"{prefix} handler for {name} is not implemented"
            logger.debug(msg)
            func = fallback
        return func

    def enter(self, prev_block: ContentBlock | None,
              block: ContentBlock | None) -> list[StackOperation]:
        # if prev and current block have the same type and subtype, do nothing
        if compare_type_and_subtype(prev_block, block):
                return []
        result: list[StackOperation] = []
        if prev_block is not None:
            # call exit handler
            func = self._get_exit_handler(prev_block["type"])
            result.extend(func(prev_block, block))
        if block is not None:
            # call enter handler
            func = self._get_enter_handler(block["type"])
            result.extend(func(prev_block, block))
        return result

    def enter_text(self, prev_block: ContentBlock | None,
                   block: TextBlock) -> list[StackOperation]:
        if not "subtype" in block:
            return []

        # call enter_text_* handler
        st = block["subtype"]
        hn = f"text_{st}"
        func = self._get_enter_handler(hn)
        return func(prev_block, block)

    def enter_text_ordered_list_item(self, prev_block: ContentBlock | None,
                   block: TextBlock) -> list[StackOperation]:
        node = self._cm.create_element("ol")
        return [{ "push_nodes": [node] }]

    def enter_text_unordered_list_item(self, prev_block: ContentBlock | None,
                   block: TextBlock) -> list[StackOperation]:
        node = self._cm.create_element("ul")
        return [{ "push_nodes": [node] }]

    def enter_text_indented(self, prev_block: ContentBlock | None,
                   block: TextBlock) -> list[StackOperation]:
        node = self._cm.create_element("blockquote", class_name="npf_indented")
        return [{ "push_nodes": [node] }]

    def exit_text(self, block: TextBlock,
                   next_block: ContentBlock | None) -> list[StackOperation]:
        if not "subtype" in block:
            return []

        # call exit_text_* handler
        st = block["subtype"]
        hn = f"text_{st}"
        func = self._get_exit_handler(hn)
        return func(block, next_block)

    def _exit_text_common(self, block: TextBlock,
                          next_block: ContentBlock) -> list[StackOperation]:
        if not "subtype" in block:
            return []
        if block["subtype"] in set(("ordered-list-item",
                                    "unordered-list-item", "indented")):
            indent_lv: int = block.get("indent_level", -1)
            if next_block is None:
                next_indent_lv = -1
            else:
                next_indent_lv = next_block.get("indent_level", -1)
            deindent = indent_lv - next_indent_lv + 1
            
            return [{ "pop_nodes": deindent }]
        return []

    def exit_text_ordered_list_item(self, block: TextBlock,
                   next_block: ContentBlock) -> list[StackOperation]:
        return self._exit_text_common(block, next_block)

    def exit_text_unordered_list_item(self, block: TextBlock,
                   next_block: ContentBlock) -> list[StackOperation]:
        return self._exit_text_common(block, next_block)

    def exit_text_indented(self, block: TextBlock,
                   next_block: ContentBlock) -> list[StackOperation]:
        return self._exit_text_common(block, next_block)

    def render_text(self, block: TextBlock, index: int) -> Node:
        if not "subtype" in block:
            return self.render_text_base(block, index)

        # call sub render function according to the subtype.
        func = self._get_render_handler("render_text", block["subtype"],
                                 fallback="render_text_base")
        return func(block, index)

    def render_inline_text(self, block: TextBlock) -> Node:
        if not "formatting" in block:
            # no formatting
            c = self._cm.get_container()
            c["children"].append(block["text"])
            return c
        # use formatting
        text_node = self._tf.format(block["formatting"], block["text"])
        c = self._cm.get_container()
        c["children"].extend(text_node)
        return c

    def render_text_base(self, block: TextBlock, index: int) -> Node:
        c = self._cm.create_element("p")
        c["children"].append(self.render_inline_text(block))
        return c

    def render_text_heading1(self, block: TextBlock, index: int) -> Node:
        c = self._cm.create_element("h1")
        c["children"].append(self.render_inline_text(block))
        return c

    def render_text_heading2(self, block: TextBlock, index: int) -> Node:
        c = self._cm.create_element("h2")
        c["children"].append(self.render_inline_text(block))
        return c

    def render_text_ordered_list_item(self, block: TextBlock, index: int) -> Node:
        c = self._cm.create_element("li")
        c["children"].append(self.render_inline_text(block))
        return c

    def render_text_unordered_list_item(self, block: TextBlock, index: int) -> Node:
        c = self._cm.create_element("li")
        c["children"].append(self.render_inline_text(block))
        return c

    def render_text_indented(self, block: TextBlock, index: int) -> Node:
        c = self._cm.create_element("p")
        c["children"].append(self.render_inline_text(block))
        return c

    def render_image(self, block: ImageBlock, index: int) -> Node:
        media_list = block["media"]
        if len(media_list) == 0:
            return self._cm.get_container()

        # find the widest image within 1280px
        media = media_list[0]
        original_media = media_list[0]
        for m in media_list:
            if m.get("has_original_dimensions", False):
                original_media = m
            if m["width"] > 1280:
                continue
            if m["width"] > media["width"]:
                media = m

        row_container = self._cm.get_row_container()
        col_container = self._cm.get_col_container()
        fig_container = self._cm.create_element("figure", class_name="tmblr-full")

        anchor_attr = {
            "cass_name": "post_media_photo_anchor",
            "data-big-photo": original_media["url"],
            "data-big-photo-height": original_media["height"],
            "data-big-photo-width": original_media["width"],
        }
        anchor_container = self._cm.create_element("a", **anchor_attr)

        img_attr = {
            "cls": "post_media_photo image",
            "src": media["url"],
            "srcset": f"{original_media["url"]} {original_media["width"]}w",
            "sizes": f"(max-width: {media["width"]}px) 100vw, {media["width"]}",
            "alt": "image",
        }
        img_container = self._cm.create_element("img", **img_attr)

        row_container["children"].append(col_container)
        col_container["children"].append(fig_container)
        fig_container["children"].append(anchor_container)
        anchor_container["children"].append(img_container)

        return row_container
