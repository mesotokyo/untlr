from typing import Any, TypedDict
import logging
logger = logging.getLogger(__name__)

type Attribute = tuple[str, str]

class Node(TypedDict):
    children: list[Any]
    
class HtmlElement(Node):
    tag_name: str
    attributes: list[Attribute]

type NodeList = list[Node]

class ContainerBuilder:
    def __init__(self):
        pass

    def _make_attr(self, **kwargs) -> list[Attribute]:
        result: list[Attribute] = []
        for k, v in kwargs.items():
            if k == "class_name":
                if v:
                    result.append(("class", str(v)))
            else:
                result.append((k, str(v)))
        return result
    
    def create_element(self, tag_name: str,
                        class_name: str = "", **kwargs) -> HtmlElement:
        return {
            "tag_name": tag_name,
            "attributes": self._make_attr(class_name=class_name, **kwargs),
            "children": []
        }

    def get_container(self) -> Node:
        return { "children": [] }

    def get_row_container(self) -> Node:
        return self.create_element("div", class_name="npf_row")

    def get_col_container(self) -> Node:
        return self.create_element("div", class_name="npf_col")
