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


LINKS = [
    {'from_domain': 'foo', 'to_domain': 'bar', 'num': '1', 'mf2_class': 'u-like-of'},
    {'from_domain': 'foo', 'to_domain': 'bar', 'num': '2'},
    {'from_domain': 'foo', 'to_domain': 'baz', 'num': '3'},
    {'from_domain': 'bar', 'to_domain': 'foo', 'num': '4', 'mf2_class': 'u-quotation-of'},
    {'from_domain': 'baz', 'to_domain': 'bar', 'num': '5'},
    {'from_domain': 'baz', 'to_domain': 'foo', 'num': '7', 'mf2_class': 'u-quotation-of'},
    {'from_domain': 'foo', 'to_domain': 'other.com', 'num': '8'},
    {'from_domain': 'more.com', 'to_domain': 'foo', 'num': '1'},
]
SITES = [
    {'domain': 'foo', 'urls': ['https://foo/ey', 'nope'], 'hcard': '{"a": "b"}'},
    {'domain': 'bar', 'descriptions': ["this is, bar's site"], 'mf2': '', 'html': ''},
]
EXTRA_1 = [
    {'domain': 'foo', 'foo': 'fooey'},
    {'domain': 'baz', 'baz': 'bazzey'},
]
EXTRA_2 = [
    {'domain': 'bar', 'bar': 'barrey'},
]
FULL = [{
    'domain': 'foo',
    'urls': ['https://foo/ey', 'nope'],
    'foo': 'fooey',
    'hcard': {'a': 'b'},
    'links_out': 14,
    'links_in': 12,
    'links': OrderedDict((
        # sorted by score, desc
        ('baz', {
            'out': {'other': 3},
            'in':  {'quotation-of': 7},
            'score': 1,
        }),
        ('bar', {
            'out': {'like-of': 1, 'other': 2},
            'in':  {'quotation-of': 4},
            'score': Decimal('.909'),  # ln(20) / ln(27)
        }),
        ('other.com', {
            'out': {'other': 8},
            'score': Decimal('.839'),  # ln(16) / ln(27)
        }),
        ('more.com', {
            'in': {'other': 1},
            'score': 0,  # ln(1) / ln(27) == 0
        }),
    )),
}, {
    'domain': 'bar',
    'descriptions': ["this is, bar's site"],
    'bar': 'barrey',
    'hcard': {},
    'links_out': 4,
    'links_in': 8,
    'links': OrderedDict((
        ('foo', {
            'out': {'quotation-of': 4},
            'in':  {'like-of': 1, 'other': 2},
            'score': 1,
        }),
        ('baz', {
            'in':  {'other': 5},
            'score': Decimal('.483'),  # ln(5) / ln(28)
        }),
    )),
}, {
    'domain': 'baz',
    'baz': 'bazzey',
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
            'score': Decimal('.604'),  # ln(10) / ln(45)
        }),
    )),
}, {
    'domain': 'more.com',
    'links_out': 1,
    'links_in': 0,
    'hcard': {},
    'links': OrderedDict((
        ('foo', {
            'out': {'other': 1},
            'score': 1,
        }),
    )),
}]

BASE = copy.deepcopy(FULL)
for site in BASE[:3]:
    site['links'] = dict(list(site['links'].items())[:1])
    site['links_truncated'] = True

INTERNAL_DOMAINS = {'foo', 'bar'}
INTERNAL = copy.deepcopy(FULL[:2])
INTERNAL[0]['links'] = {'bar': INTERNAL[0]['links']['bar']}
INTERNAL[1]['links'] = {'foo': INTERNAL[1]['links']['foo']}


class MakeWebTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.sites = copy.deepcopy(SITES)
        self.links = copy.deepcopy(LINKS)
        self.full = copy.deepcopy(FULL)

    def test_full(self):
        got = list(make_web.make_full(self.sites, self.links, EXTRA_1, EXTRA_2))
        for expected, actual in itertools.zip_longest(FULL, got):
            self.assertEqual(expected, actual)

    def test_full_tags(self):
        self.sites = [
            {'domain': 'tantek.com'},
            {'domain': 'x.indiewebify.me'},
            {'domain': 'y.withknown.com'},
        ]

        got = list(make_web.make_full(self.sites, self.links))
        self.assertEqual(['bridgy', 'elder', 'founder', 'IRC', 'webmention.io'],
                         got[0]['tags'])
        self.assertEqual(['community', 'tool'], got[1]['tags'])
        self.assertNotIn('tags', got[2])

    def test_full_server(self):
        self.sites[0]['servers'] = ['apache', 'nginx']
        self.sites[1].update({
            'servers': ['apache'],
            'rel_generators': ['Known https://withknown.com'],
            'meta_generators': ['Known http://withknown.com'],
        })
        self.sites.append({
            'domain': 'biff',
            'meta_generators': ['WordPress'],
        })

        got = list(make_web.make_full(self.sites, self.links))
        self.assertEqual(['apache', 'nginx'], got[0]['servers'])
        self.assertNotIn('tags', got[0])

        self.assertNotIn('rel_generators', got[1])
        self.assertNotIn('meta_generators', got[1])
        self.assertEqual(['apache', 'Known'], got[1]['servers'])
        self.assertEqual(['Known'], got[1]['tags'])

        self.assertNotIn('meta_generators', got[1])
        self.assertEqual(['WordPress'], got[2]['servers'])
        self.assertEqual(['WordPress'], got[2]['tags'])

    def test_full_fetch_crawl_times(self):
        self.sites[0]['fetch_time'] = '2017-05-19T23:54:47.067044'
        self.sites[1].update({
            'crawl_start': '1493134946',
            'crawl_end': '1493138613',
        })

        got = list(make_web.make_full(self.sites, self.links))

        self.assertEqual('2017-05-19T23:54:47.067044', got[0]['crawl_start'])
        self.assertEqual('2017-05-19T23:54:47.067044', got[0]['crawl_end'])
        self.assertNotIn('fetch_time', got[0])

        self.assertEqual('2017-04-25T15:42:26', got[1]['crawl_start'])
        self.assertEqual('2017-04-25T16:43:33', got[1]['crawl_end'])

    @patch.object(make_web, 'MAX_BASE_LINKS', new=1)
    def test_base(self):
        got = make_web.make_base(self.full)
        for expected, actual in itertools.zip_longest(BASE, got):
            self.assertEqual(expected, actual)

    def test_internal(self):
        got = make_web.make_internal(self.full, INTERNAL_DOMAINS)
        for expected, actual in itertools.zip_longest(INTERNAL, got):
            self.assertEqual(expected, actual)

    def test_json_encode_decimal_0(self):
        encoded = json.dumps(list(make_web.make_full(self.sites, self.links)))
        self.assertIn('"score": 0}', encoded)
        self.assertNotIn('"score": 0E+', encoded)
