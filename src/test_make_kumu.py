#!/usr/bin/env python3
"""Unit tests for make_kumu.py.
"""
import copy
import io
import unittest

import make_kumu
import test_make_web

SITES = copy.deepcopy(test_make_web.FULL)
SITES[0].update({
    'tags': ['a', 'b'],
    'num_pages': 99,
    'servers': ['Apache', 'Nginx'],
    'mf2_classes': ['h-card', 'h-event'],
})

ELEMENTS = """\
Label,URL,Title,Description,Tags,Image,LinksIn,LinksOut,Pages,Server,Mf2Classes\r
foo,https://foo/ey,,,a|b,,12,14,99,Apache|Nginx,h-card|h-event\r
bar,,,"this is, bar's site",token,,8,4,,,\r
baz,,,,,,3,12,,,\r
more.com,,,,,,0,1,,,\r
"""
CONNECTIONS = """\
From,To,Type,Label,Tags,Links,Strength\r
foo,baz,,,other,3,1\r
foo,bar,,,like|other,3,0.909\r
foo,other.com,,,other,8,0.839\r
bar,foo,,,quotation,4,1\r
baz,foo,,,quotation,7,1\r
baz,bar,,,other,5,0.604\r
more.com,foo,,,other,1,1\r
"""


class MakeKumuTest(unittest.TestCase):
    maxDiff = None

    def test_make(self):
        elems = io.StringIO()
        conns = io.StringIO()
        make_kumu.make(SITES, elems, conns)

        self.assertMultiLineEqual(ELEMENTS, elems.getvalue())
        self.assertMultiLineEqual(CONNECTIONS, conns.getvalue())
