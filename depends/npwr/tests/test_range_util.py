import unittest
import sys
import os.path
sys.path.append(os.path.abspath("src"))

from spycy_bdd import BddTest
from intervaltree import IntervalTree

from npwr.range_util import (RangedTreeNode, split_overwrapped_range,
                             RangedItem, _is_intersected, _is_in, make_tree)

class TestItem(RangedItem):
    value: str

def _mk_node(start: int, end: int, val: str,
                    children: list[RangedTreeNode[TestItem]] = []) -> RangedTreeNode[TestItem]:
    return {
        "item": { "start": start, "end": end, "value": val },
        "children": children
    }

def _mk_i_tree(items):
    t = IntervalTree()
    for item in items:
        t.addi(item[0], item[1], item[2])
    return t

class RangeUtilTest(BddTest):
    def setUp(self):
        pass

    def scenario_is_intersected1(self, given, when, then):
        a = { "start": 1, "end": 3, "v": "a"}
        b = { "start": 2, "end": 3, "v": "b"}
        given(a=a, b=b,
              _is_intersected=_is_intersected)
        when._is_intersected(given.a, given.b)
        then.it.should.be.false

    def scenario_is_intersected2(self, given, when, then):
        a = { "start": 1, "end": 3, "v": "a"}
        b = { "start": 2, "end": 4, "v": "b"}
        given(a=a, b=b,
              _is_intersected=_is_intersected)
        when._is_intersected(given.a, given.b)
        then.it.should.be.true

    def scenario_is_intersected3(self, given, when, then):
        a = { "start": 2, "end": 3, "v": "a"}
        b = { "start": 1, "end": 3, "v": "b"}
        given(a=a, b=b,
              _is_intersected=_is_intersected)
        when._is_intersected(given.a, given.b)
        then.it.should.be.false

    def scenario_is_intersected4(self, given, when, then):
        a = { "start": 2, "end": 4, "v": "a"}
        b = { "start": 1, "end": 3, "v": "b"}
        given(a=a, b=b,
              _is_intersected=_is_intersected)
        when._is_intersected(given.a, given.b)
        then.it.should.be.true

    def scenario_is_intersected5(self, given, when, then):
        a = { "start": 2, "end": 4, "v": "a"}
        b = { "start": 2, "end": 4, "v": "b"}
        given(a=a, b=b,
              _is_intersected=_is_intersected)
        when._is_intersected(given.a, given.b)
        then.it.should.be.false
        
    def scenario_is_intersected6(self, given, when, then):
        a = { "start": 1, "end": 2, "v": "a"}
        b = { "start": 1, "end": 4, "v": "b"}
        given(a=a, b=b,
              _is_intersected=_is_intersected)
        when._is_intersected(given.a, given.b)
        then.it.should.be.false

    def scenario_is_intersected7(self, given, when, then):
        a = { "start": 1, "end": 4, "v": "a"}
        b = { "start": 1, "end": 2, "v": "b"}
        given(a=a, b=b,
              _is_intersected=_is_intersected)
        when._is_intersected(given.a, given.b)
        then.it.should.be.false

    def scenario_is_intersected8(self, given, when, then):
        a = { "start": 4, "end": 7, "v": "a"}
        b = { "start": 3, "end": 4, "v": "b"}
        given(a=a, b=b,
              _is_intersected=_is_intersected)
        when._is_intersected(given.a, given.b)
        then.it.should.be.false

    def scenario_is_intersected9(self, given, when, then):
        a = { "start": 4, "end": 7, "v": "a"}
        b = { "start": 5, "end": 6, "v": "b"}
        given(a=a, b=b,
              _is_intersected=_is_intersected)
        when._is_intersected(given.a, given.b)
        then.it.should.be.false

    def scenario_is_in1(self, given, when, then):
        a = { "start": 6,"end": 7, "v": "a"}
        b = { "start": 5, "end": 9, "v": "b"}
        given(a=a, b=b,
              _is_in=_is_in)
        when._is_in(given.a, given.b)
        then.it.should.be.true

    def scenario_is_in2(self, given, when, then):
        a = { "start": 5, "end": 9, "v": "b"}
        b = { "start": 6,"end": 7, "v": "a"}
        given(a=a, b=b,
              _is_in=_is_in)
        when._is_in(given.a, given.b)
        then.it.should.be.false

    def scenario_is_in3(self, given, when, then):
        a = { "start": 5, "end": 7, "v": "b"}
        b = { "start": 6,"end": 9, "v": "a"}
        given(a=a, b=b,
              _is_in=_is_in)
        when._is_in(given.a, given.b)
        then.it.should.be.false

    def make_test_data(self, items: list[tuple[int, int, str]]) -> list[TestItem]:
        r: list[TestItem] = [{"start": x[0], "end": x[1], "value": x[2]} for x in items]
        return r
        
    def scenario_single_item(self, given, when, then):
        items = [(1, 2, "a")]
        test_data = self.make_test_data(items)
        expected_data = self.make_test_data(items)
        given(split_overwrapped_range=split_overwrapped_range,
              test_data=test_data)
        when.split_overwrapped_range(given.test_data)
        then.it.should.equal(expected_data)
        
    def scenario_not_overwrapped(self, given, when, then):
        items = [(1, 2, "a"), (1, 4, "b")]
        test_data = self.make_test_data(items)
        expected_data = self.make_test_data(items)
        given(split_overwrapped_range=split_overwrapped_range,
              test_data=test_data)
        when.split_overwrapped_range(given.test_data)
        then.it.should.equal(expected_data)

    def scenario_split_overwrapped_range(self, given, when, then):
        items = [(1, 2, "a"), (1, 4, "b"), (3, 7, "c")]
        expected = [(1, 2, "a"), (1, 4, "b"), (3, 4, "c"), (4, 7, "c")]
        test_data = self.make_test_data(items)
        expected_data = self.make_test_data(expected)
        given(split_overwrapped_range=split_overwrapped_range,
              test_data=test_data)
        when.split_overwrapped_range(given.test_data)
        then.it.should.equal(expected_data)

    def scenario_split_overwrapped_range2(self, given, when, then):
        items = [(1, 2, "a"), (1, 4, "b"), (3, 7, "c"), (5, 7, "d"), (6, 8, "e")]
        expected = [(1, 2, "a"), (1, 4, "b"), (3, 4, "c"), (4, 7, "c"),
                    (5, 7, "d"), (6, 7, "e"), (7, 8, "e")]
        test_data = self.make_test_data(items)
        expected_data = self.make_test_data(expected)
        given(split_overwrapped_range=split_overwrapped_range,
              test_data=test_data)
        when.split_overwrapped_range(given.test_data)
        then.it.should.equal(expected_data)

    def scenario_make_tree1(self, given, when, then):
        items = [(1, 2, "a"), (1, 4, "b"), (3, 4, "c")]
        test_data = self.make_test_data(items)
        expected: list[RangedTreeNode] = [
            _mk_node(1, 4, "b", [
                _mk_node(1, 2, "a"), _mk_node(3, 4, "c")
            ]),
        ]
        
        given(make_tree=make_tree,
              test_data=test_data)
        when.make_tree(given.test_data)
        then.it.should.equal(expected)
        
    def scenario_make_tree2(self, given, when, then):
        items = [(1, 2, "a"), (1, 4, "b"), (3, 4, "c"), (4, 7, "c")]
        test_data = self.make_test_data(items)
        expected: list[RangedTreeNode] = [
            _mk_node(1, 4, "b", [
                _mk_node(1, 2, "a"), _mk_node(3, 4, "c")
            ]),
            _mk_node(4, 7, "c" ),
        ]
        
        given(make_tree=make_tree,
              test_data=test_data)
        when.make_tree(given.test_data)
        then.it.should.equal(expected)
        
    def scenario_make_tree3(self, given, when, then):
        items = [(1, 2, "a"), (1, 4, "b"), (3, 4, "c"), (4, 7, "c"),
                    (5, 7, "d")]
        test_data = self.make_test_data(items)
        expected: list[RangedTreeNode] = [
            _mk_node(1, 4, "b", [
                _mk_node(1, 2, "a"), _mk_node(3, 4, "c")
            ]),
            _mk_node(4, 7, "c", [
                _mk_node(5,  7, "d"),
            ]),
        ]
        
        given(make_tree=make_tree,
              test_data=test_data)
        when.make_tree(given.test_data)
        then.it.should.equal(expected)
        
    def scenario_make_tree4(self, given, when, then):
        items = [(1, 2, "a"), (1, 4, "b"), (3, 4, "c"), (4, 7, "c"),
                    (5, 7, "d"), (6, 7, "e")]
        test_data = self.make_test_data(items)
        expected: list[RangedTreeNode] = [
            _mk_node(1, 4, "b", [
                _mk_node(1, 2, "a"), _mk_node(3, 4, "c")
            ]),
            _mk_node(4, 7, "c", [
                _mk_node(5,  7, "d", [ _mk_node(6, 7, "e") ]),
            ]),
        ]
        
        given(make_tree=make_tree,
              test_data=test_data)
        when.make_tree(given.test_data)
        then.it.should.equal(expected)
        
    def scenario_make_tree5(self, given, when, then):
        items = [(1, 2, "a"), (1, 4, "b"), (3, 4, "c"), (4, 7, "c"),
                    (5, 7, "d"), (6, 7, "e"), (7, 8, "e")]
        test_data = self.make_test_data(items)
        expected: list[RangedTreeNode] = [
            _mk_node(1, 4, "b", [
                _mk_node(1, 2, "a"), _mk_node(3, 4, "c")
            ]),
            _mk_node(4, 7, "c", [
                _mk_node(5,  7, "d", [ _mk_node(6, 7, "e") ]),
            ]),
            _mk_node(7, 8, "e"),
        ]
        
        given(make_tree=make_tree,
              test_data=test_data)
        when.make_tree(given.test_data)
        then.it.should.equal(expected)
        
    def scenario_make_tree6(self, given, when, then):
        items = [(1, 2, "a"), (1, 4, "b"), (3, 4, "c"), (4, 7, "c"),
                    (5, 7, "d"), (5, 7, "f"), (6, 7, "e"), (7, 8, "e")]
        test_data = self.make_test_data(items)
        expected: list[RangedTreeNode] = [
            _mk_node(1, 4, "b", [
                _mk_node(1, 2, "a"), _mk_node(3, 4, "c")
            ]),
            _mk_node(4, 7, "c", [
                _mk_node(5,  7, "d", [
                    _mk_node(5, 7, "f", [ _mk_node(6, 7, "e") ])
                ]),
            ]),
            _mk_node(7, 8, "e"),
        ]
        
        given(make_tree=make_tree,
              test_data=test_data)
        when.make_tree(given.test_data)
        then.it.should.equal(expected)
