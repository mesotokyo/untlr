import unittest
import sys
import os.path
sys.path.append(os.path.abspath("src"))

from .spycy_bdd import BddTest

from npwr import TextFormatter
from npwr.block_renderer import (TextBlock, TextFormatter,
                                 TextFormatting, ContainerBuilder)
from npwr.html_renderer import render_html

class TextFormattertTest(BddTest):
    def setUp(self):
        cm = ContainerBuilder()
        self.fmtr = TextFormatter(cm)
        
    def scenario_without_formatting(self, given, when, then):
        fmts: list[TextFormatting] = []
        txt="foo_bar_baz",
        given(render_html=render_html)
        when.render_html(self.fmtr.format(fmts, "foo_bar_baz"))
        then.it.should.equal("foo_bar_baz")

    def scenario_format_with_link_formatting1(self, given, when, then):
        url = "http://example.com/"
        fmts: list[TextFormatting] = [{
            "start": 0,
            "end": 3,
            "type": "link",
            "url": url,
        }]
        txt="foo_bar_baz",
        given(render_html=render_html)
        when.render_html(self.fmtr.format(fmts, "foo_bar_baz"))
        then.it.should.equal(f"""<a href="{url}">foo</a>_bar_baz""")

    def scenario_format_with_link_formatting2(self, given, when, then):
        url1 = "http://example.com/"
        url2 = "http://example.com/foo"
        fmts: list[TextFormatting] = [
            {
                "start": 0,
                "end": 3,
                "type": "link",
                "url": url1,
            },
            {
                "start": 5,
                "end": 8,
                "type": "link",
                "url": url2,
            },
        ]
        txt="foo_bar_baz",
        given(render_html=render_html)
        when.render_html(self.fmtr.format(fmts, "foo_bar_baz"))
        then.it.should.equal(f"""<a href="{url1}">foo</a>_b<a href="{url2}">ar_</a>baz""")

