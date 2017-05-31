#!/usr/bin/env python3
"""Unit tests for make_site_files.py.
"""
from io import StringIO
import itertools
import json
import os
import unittest

import make_site_files

# prevent python 3 unittest from eliding assertEqual diffs with '...[X chars]...'
# (TestCase.maxDiff doesn't affect it)
# http://stackoverflow.com/a/34117192/186123
unittest.util._MAX_LENGTH = 2000

def json_file(objs):
    """BigQuery JSON files are one JSON object per line."""
    return StringIO('\n'.join(json.dumps(obj) for obj in objs))

LINKS = (
    {'from_domain': 'foo', 'to_domain': 'bar', 'num': '1', 'mf2_class': 'u-like-of'},
    {'from_domain': 'foo', 'to_domain': 'bar', 'num': '2'},
    {'from_domain': 'foo', 'to_domain': 'baz', 'num': '3'},
    {'from_domain': 'bar', 'to_domain': 'foo', 'num': '4', 'mf2_class': 'u-quotation-of'},
    {'from_domain': 'baz', 'to_domain': 'bar', 'num': '5'},
    {'from_domain': 'baz', 'to_domain': 'foo', 'num': '7', 'mf2_class': 'u-quotation-of'},
)
SITES = (
    {'domain': 'foo', 'x': 'y'},
    {'domain': 'bar', 'u': 'v'},
)
EXPECTED = [{
    'domain': 'foo',
    'x': 'y',
    'outbound_links': 6,
    'inbound_links': 11,
    'links': {
        'bar': {
            'outbound': {'u-like-of': 1, None: 2},
            'inbound':  {'u-quotation-of': 4},
            'score': 2.0,
        },
        'baz': {
            'outbound': {None: 3},
            'inbound':  {'u-quotation-of': 7},
            'score': 2.7,
        },
    },
}, {
    'domain': 'bar',
    'u': 'v',
    'outbound_links': 4,
    'inbound_links': 8,
    'links': {
        'foo': {
            'outbound': {'u-quotation-of': 4},
            'inbound':  {'u-like-of': 1, None: 2},
            'score': 2.8,
        },
        'baz': {
            'outbound': {},
            'inbound':  {None: 5},
            'score': .5,
        },
    },
}, {
    'domain': 'baz',
    'outbound_links': 12,
    'inbound_links': 3,
    'links': {
        'bar': {
            'outbound': {None: 5},
            'inbound': {},
            'score': 1.0,
        },
        'foo': {
            'outbound': {'u-quotation-of': 7},
            'inbound':  {None: 3},
            'score': 4.5,
        },
    },
}]


class MakeDataFilesTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.addTypeEqualityFunc(float, 'assertAlmostEqual')

    def test_make(self):
        got = make_site_files.make(json_file(SITES), json_file(LINKS))
        for expected, actual in itertools.zip_longest(EXPECTED, got):
            self.assertEqual(expected, actual)
