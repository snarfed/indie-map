#!/usr/bin/env python3
"""Unit tests for make_kumu.py.
"""
import copy
import io
import unittest

import make_kumu
import test_make_web

ELEMENTS = """\
Label,URL,Title,Description,Tags,Image,LinksIn,LinksOut\r
foo,https://foo/ey,,,,,12,14\r
bar,,,"this is, bar's site",,,8,4\r
baz,,,,,,3,12\r
more.com,,,,,,0,1\r
"""
CONNECTIONS = """\
From,To,Type,Label,Tags,Links,Strength\r
foo,baz,,,other,3,1\r
foo,bar,,,like|other,3,0.909\r
foo,other.com,,,other,8,0.839\r
foo,more.com,,,,0,0\r
bar,foo,,,quotation,4,1\r
bar,baz,,,,0,0.483\r
baz,foo,,,quotation,7,1\r
baz,bar,,,other,5,0.604\r
more.com,foo,,,other,1,1\r
"""


class MakeKumuTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.full = copy.deepcopy(test_make_web.FULL)

    def test_make(self):
        elems = io.StringIO()
        conns = io.StringIO()
        make_kumu.make(self.full, elems, conns)

        self.assertMultiLineEqual(ELEMENTS, elems.getvalue())
        self.assertMultiLineEqual(CONNECTIONS, conns.getvalue())
