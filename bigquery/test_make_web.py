#!/usr/bin/env python3
"""Unit tests for make_site_files.py.
"""
from collections import OrderedDict
import copy
import decimal
from decimal import Decimal
from io import StringIO
import itertools
import simplejson as json
import os
import unittest
from unittest.mock import patch

import make_web

# prevent python 3 unittest from eliding assertEqual diffs with '...[X chars]...'
# (TestCase.maxDiff doesn't affect it)
# http://stackoverflow.com/a/34117192/186123
unittest.util._MAX_LENGTH = 2000

decimal.getcontext().prec = 3

def json_file(objs):
    """BigQuery JSON files are one JSON object per line."""
    return StringIO('\n'.join(json.dumps(obj) for obj in objs))

LINKS = [
    {'from_domain': 'foo', 'to_domain': 'bar', 'num': '1', 'mf2_class': 'u-like-of'},
    {'from_domain': 'foo', 'to_domain': 'bar', 'num': '2'},
    {'from_domain': 'foo', 'to_domain': 'baz', 'num': '3'},
    {'from_domain': 'bar', 'to_domain': 'foo', 'num': '4', 'mf2_class': 'u-quotation-of'},
    {'from_domain': 'baz', 'to_domain': 'bar', 'num': '5'},
    {'from_domain': 'baz', 'to_domain': 'foo', 'num': '7', 'mf2_class': 'u-quotation-of'},
    {'from_domain': 'foo', 'to_domain': 'other.com', 'num': '8'},
]
SITES = [
    {'domain': 'foo', 'x': 'y', 'hcard': '{"a": "b"}'},  # hcard is decoded
    {'domain': 'bar', 'u': 'v', 'mf2': '', 'html': ''},  # mf2/html are stripped
]
FULL = [{
    'domain': 'foo',
    'x': 'y',
    'hcard': {'a': 'b'},
    'links_out': 14,
    'links_in': 11,
    'links': OrderedDict((
        # sorted by score, desc
        ('baz', {
            'out': {'other': 3},
            'in':  {'quotation-of': 7},
            'score': 1,  # 2.7
        }),
        ('bar', {
            'out': {'like-of': 1, 'other': 2},
            'in':  {'quotation-of': 4},
            'score': Decimal('2') / Decimal('2.7'),
        }),
        ('other.com', {
            'out': {'other': 8},
            'score': Decimal('1.6') / Decimal('2.7'),
        }),
    )),
}, {
    'domain': 'bar',
    'u': 'v',
    'hcard': {},
    'links_out': 4,
    'links_in': 8,
    'links': OrderedDict((
        ('foo', {
            'out': {'quotation-of': 4},
            'in':  {'like-of': 1, 'other': 2},
            'score': 1,  # 2.8
        }),
        ('baz', {
            'in':  {'other': 5},
            'score': Decimal('.5') / Decimal('2.8'),
        }),
    )),
}, {
    'domain': 'baz',
    'hcard': {},
    'links_out': 12,
    'links_in': 3,
    'links': OrderedDict((
        ('foo', {
            'out': {'quotation-of': 7},
            'in':  {'other': 3},
            'score': 1,  # 4.5
        }),
        ('bar', {
            'out':  {'other': 5},
            'score': Decimal('1') / Decimal('4.5'),
        }),
    )),
}]


class MakeDataFilesTest(unittest.TestCase):
    maxDiff = None

    def test_full(self):
        got = make_web.make_full(SITES, LINKS)
        for expected, actual in itertools.zip_longest(FULL, got):
            self.assertEqual(expected, actual)

    @patch.object(make_web, 'MAX_BASE_LINKS', new=1)
    def test_base(self):
        base = copy.deepcopy(FULL)
        for site in base:
            site['links'] = dict(list(site['links'].items())[:1])
            site['links_truncated'] = True

        got = make_web.make_base(FULL)
        for expected, actual in itertools.zip_longest(base, got):
            self.assertEqual(expected, actual)

    def test_internal(self):
        internal = copy.deepcopy(FULL)
        del internal[0]['links']['other.com']

        got = make_web.make_internal(SITES, FULL)
        for expected, actual in itertools.zip_longest(internal, got):
            self.assertEqual(expected, actual)
