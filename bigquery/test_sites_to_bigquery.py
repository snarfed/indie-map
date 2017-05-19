#!/usr/bin/env python3
"""Unit tests for sites_to_bigquery.py.
"""
from io import StringIO
import json
import os
import unittest
from unittest.mock import patch

import mf2py
import requests
import sites_to_bigquery

# prevent python 3 unittest from eliding assertEqual diffs with '...[X chars]...'
# (TestCase.maxDiff doesn't affect it)
# http://stackoverflow.com/a/34117192/186123
unittest.util._MAX_LENGTH = 2000


HTML = """\
<!DOCTYPE html>
<html>
<head>
  <title>A Title</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="A meta description">
  <link rel="shortcut icon" href="icon.jpg" />
  <link rel="webmention" href="https://webmention.herokuapp.com/api/webmention" />
  <link rel="canonical" href="http://foo.com/canonical" />
</head>
<body>
  <a rel="me" href="http://a/silo">
  <a rel="me" href="http://b/silo">
  <article class="h-feed">
  </article>
  <div class="h-card">
    <a href="/" class="p-name">My Name</a>
    <p class="p-note">About me</p>
  </div>
</body>
</html>
"""
RESPONSE = requests.Response()
RESPONSE._content = HTML.encode('utf-8')
RESPONSE.url = 'http://foo.com/'


class SitesToBigQueryTest(unittest.TestCase):

    maxDiff = None

    @patch.object(requests, 'get', return_value=RESPONSE)
    def test_complete(self, mock_get):
        actual = sites_to_bigquery.convert('orig.com')
        self.assertEqual({
            'domain': 'orig.com',
            'urls': ['http://foo.com/', 'http://foo.com/canonical'],
            'names': ['My Name', 'A Title'],
            'descriptions': ['About me', 'A meta description'],
            'pictures': ['http://foo.com/icon.jpg'],
            'hcard': json.dumps({
                'type': ['h-card'],
                'properties': {
                    'name': ['My Name'],
                    'url': ['http://foo.com/'],
                    'note': ['About me'],
                },
            }, sort_keys=True),
            'mf2': json.dumps(mf2py.parse(doc=HTML, url='http://foo.com'),
                              sort_keys=True),
            'rel_mes': ['http://a/silo', 'http://b/silo'],
            'html': HTML,
            'fetch_time': actual['fetch_time']
        }, actual)

