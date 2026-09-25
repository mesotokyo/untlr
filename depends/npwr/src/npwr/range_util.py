from __future__ import annotations
from typing import TypedDict, Required, NotRequired
from operator import itemgetter

class RangedItem(TypedDict, total=False):
    start: Required[int]
    end: Required[int]

class RangedTreeNode[X: RangedItem](TypedDict):
    children: list[RangedTreeNode]
    item: X

def _is_intersected(a: RangedItem, b: RangedItem) -> bool:
    # Common edge
    if a["start"] == b["start"] or a["end"] == b["end"]:
        return False
    # Wrapped
    if (a["start"] <= b["start"] and b["end"] <= a["end"]):
        return False
    if (b["start"] <= a["start"] and a["end"] <= b["end"]):
        return False
    # Completely separated
    if (b["end"] <= a["start"] or a["end"] <= b["start"]):
        return False
    # Otherwise
    return True
    
def _is_in(a: RangedItem, b: RangedItem) -> bool:
    """Returns True if a is in b. Otherwise, False."""
    return b["start"] <= a["start"] and a["end"] <= b["end"]

def split_overwrapped_range(items: list[RangedItem]):
    # Check overwrap and split if needed
    # Example:
    #      [(1, 2, a), (1, 4, b), (3, 7, c), (5, 7, d), (6, 8, e)]
    # -> [(1, 2, a), (1, 4, b), (3, 4, c), (4, 7, c), (5, 7, d), (6, 8, e)]
    # -> [(1, 2, a), (1, 4, b), (3, 4, c), (4, 7, c), (5, 7, d), (6, 7, e), (7, 8, e)]

    if len(items) < 2:
        return items

    completed = False
    while not completed:
        # Sort items by start and end, ascend order
        items = sorted(items, key=itemgetter("start", "end"))
        prev = items[0]

        # check items
        completed = True
        #print(items)
        for index, item in enumerate(items):
            if index == 0:
                continue
            if _is_intersected(item, prev):
                new_item = item.copy()
                new_item["start"] = prev["end"]
                item["end"] = prev["end"]
                items.insert(index, new_item)
                completed = False
                break
            prev = item

    return items

def make_tree(items: list[RangedItem]) -> list[RangedTreeNode]:
    """items is a list that does not contain overwrapped range.
    Example:
    [(1, 2, a), (1, 4, b), (3, 4, c), (4, 7, c), (5, 7, d), (6, 7, e), (7, 8, e)]
    -> [(1, 4, b)[(1, 2, a)], (3, 4, c), (4, 7, c), (5, 7, d), (6, 7, e), (7, 8, e)]
    -> [(1, 4, b)[(1, 2, a), (3, 4, c)], (4, 7, c), (5, 7, d), (6, 7, e), (7, 8, e)]
    -> [(1, 4, b)[(1, 2, a), (3, 4, c)], (4, 7, c)[(5, 7, d)], (6, 7, e), (7, 8, e)]
    -> [(1, 4, b)[(1, 2, a), (3, 4, c)], (4, 7, c)[(5, 7, d)[(6, 7, e)]], (7, 8, e)]
    """
    root: list[RangedTreeNode] = []
    if not items:
        return root
    wrapped: list[RangedTreeNode] = [ { "item": x, "children": [] } for x in items]

    prev = wrapped[0]
    for index, item in enumerate(wrapped):
        if index == 0:
            continue
        if _is_in(prev["item"], item["item"]):
            item["children"].append(prev)
            prev = item
            continue
        if _is_in(item["item"], prev["item"]):
            c = prev
            while True:
                if not c["children"]:
                    break
                if not _is_in(item["item"], c["children"][-1]["item"]):
                    break
                c = c["children"][-1]
            c["children"].append(item)
            continue
        root.append(prev)
        prev = item
    root.append(prev)
    return root
