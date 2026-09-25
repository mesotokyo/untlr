from typing import TypedDict, NotRequired, Any, TypeGuard

class RowLayout(TypedDict):
    blocks: list[int]

class Layout(TypedDict):
    type: str
    display: list[RowLayout]
    truncate_after: NotRequired[int]

class ContentBlock(TypedDict):
    type: str

class TextFormatting(TypedDict):
    start: int
    end: int
    type: str
    url: NotRequired[str]

class TextBlock(ContentBlock):
    text: str
    subtype: NotRequired[str]
    formatting: NotRequired[list[TextFormatting]]
    indent_level: NotRequired[int]

def is_text_block(block: ContentBlock | None) -> TypeGuard[TextBlock]:
    return block is not None and block["type"] == "text"

class MediaContent(TypedDict):
    type: str
    url: str
    width: int
    height: int
    has_original_dimensions: NotRequired[bool]
    
class ImageBlock(ContentBlock):
    media: list[MediaContent]
    alt_text: NotRequired[str]
    caption: NotRequired[str]
    
def is_image_block(block: ContentBlock | None) -> TypeGuard[ImageBlock]:
    return block is not None and block["type"] == "image"

class NPFDict(TypedDict):
    content: list[ContentBlock]
    layout: NotRequired[list[Layout]]

def _compare_props(block1: ContentBlock,
                   block2: ContentBlock, props: list[str]) -> bool:
    """
    If both block1 and block2 have same property,
    and values of the property are the same, returns True.
    """
    for prop in props:
        if block1.get(prop, None) != block2.get(prop, None):
            return False
    return True

def compare_type_and_subtype(block1: ContentBlock | None,
                             block2: ContentBlock | None) -> bool:
    if block1 is None or block2 is None:
        return False
    if block1["type"] != block2["type"]:
        return False
    if block1["type"] == "text":
        return _compare_props(block1, block2, ["subtype", "indent_level"])
    return True

    
# Exceptions
class ContentNotExistsError(Exception): pass
class LayoutNotSupportedError(Exception): pass

    
