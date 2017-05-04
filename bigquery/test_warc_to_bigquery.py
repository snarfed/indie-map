# coding=utf-8
"""Unit tests for warc_to_bigquery.py.
"""
import copy
from cStringIO import StringIO
import gzip
import os
import unittest

import simplejson as json
import warc

import warc_to_bigquery


WARC_HEADER = """\
WARC/1.0\r
WARC-Type: warcinfo\r
WARC-Date: 2014-09-05T11:18:02Z\r
WARC-Record-ID: <urn:uuid:ac993447-4652-47a0-be86-c14c7dc60e5e>\r
Content-Length: 371\r
Content-Type: application/warc-fields\r
WARC-Filename: CC-MAIN-20140820021320-00000-ip-10-180-136-8.ec2.internal.warc.gz\r
\r
robots: classic\r
hostname: ip-10-180-136-8.ec2.internal\r
software: Nutch 1.6 (CC)/CC WarcExport 1.0\r
isPartOf: CC-MAIN-2014-35\r
operator: CommonCrawl Admin\r
description: Wide crawl of the web with URLs provided by Blekko for August 2014\r
publisher: CommonCrawl\r
format: WARC File Format 1.0\r
conformsTo: http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1_latestdraft.pdf\r
"""
WARC_REQUEST = """\
WARC/1.0\r
WARC-Type: request\r
WARC-Date: 2014-08-20T06:36:13Z\r
WARC-Record-ID: <urn:uuid:0fa7a21c-8de1-44ef-a896-f39aad9fb915>\r
Content-Length: 317\r
Content-Type: application/http; msgtype=request\r
WARC-Warcinfo-ID: <urn:uuid:ac993447-4652-47a0-be86-c14c7dc60e5e>\r
WARC-IP-Address: 85.214.72.216\r
WARC-Target-URI: http://0pointer.de/photos/?gallery=Chorin%202010-10&photo=119&exif_style=&show_thumbs=\r
\r
GET /photos/?gallery=Chorin%202010-10&photo=119&exif_style=&show_thumbs= HTTP/1.0\r
Host: 0pointer.de\r
Accept-Encoding: x-gzip, gzip, deflate\r
User-Agent: CCBot/2.0 (http://commoncrawl.org/faq/)\r
Accept-Language: en-us,en-gb,en;q=0.7,*;q=0.3\r
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r
\r
"""
WARC_RESPONSE = """\
WARC/1.0\r
Content-Length: %s\r
WARC-Concurrent-To: <urn:uuid:0fa7a21c-8de1-44ef-a896-f39aad9fb915>\r
WARC-Date: 2014-08-20T06:36:13Z\r
WARC-Payload-Digest: sha1:MOKD54JQHY4EWHNOJLT6IXM3ZTACA3CJ\r
WARC-IP-Address: 85.214.72.216\r
WARC-Block-Digest: sha1:VEYQQ2LH25SNUWZNVD4KA7EZWRKWK4HG\r
WARC-Record-ID: <urn:uuid:f95806a3-162c-41d5-a7d5-a6af7084409b>\r
WARC-Target-URI: %s\r
WARC-Warcinfo-ID: <urn:uuid:ac993447-4652-47a0-be86-c14c7dc60e5e>\r
Content-Type: application/http; msgtype=response\r
WARC-Type: response\r
"""
HTTP_HEADERS = {
  'Date': 'Wed, 20 Aug 2014 06:36:13 GMT',
  'Server': 'Apache',
  'X-Powered-By': 'PHP/5.3.8-1+b1',
  'Connection': 'close',
  'Content-Type': 'text/html; charset=utf-8',
}
HTML = """\
<!DOCTYPE html>
<html>
<head>
%s
</head>
<body>%s</body>
</html>"""
WARC_METADATA = """\
WARC/1.0\r
WARC-Type: metadata\r
WARC-Date: 2014-08-20T06:36:13Z\r
WARC-Record-ID: <urn:uuid:e32aadef-5864-48e5-8829-c1a22223fb86>\r
Content-Length: 20\r
Content-Type: application/warc-fields\r
WARC-Warcinfo-ID: <urn:uuid:ac993447-4652-47a0-be86-c14c7dc60e5e>\r
WARC-Concurrent-To: <urn:uuid:f95806a3-162c-41d5-a7d5-a6af7084409b>\r
WARC-Target-URI: http://0pointer.de/photos/?gallery=Chorin%202010-10&photo=119&exif_style=&show_thumbs=\r
\r
fetchTimeMs: 476\r
\r
"""

EMPTY_MF2 = json.dumps({'items': [], 'rel-urls': {}, 'rels': {}}, indent=2)
BIGQUERY_JSON = {
  'url': 'http://foo',
  'time': '2014-08-20T06:36:13Z',
  'headers': sorted([list(it) for it in HTTP_HEADERS.items()] +
                    [['Content-Length', str(len(HTML % ('', 'foo')))]]),
  'html': HTML % ('', 'foo'),
  'mf2': EMPTY_MF2,
  'mf2_classes': [],
  'links': [],
  'rels': {},
  'u_urls': [],
}

def warc_response(body, url, html_head='', extra_headers=None):
  html = HTML % (html_head, body)
  headers = copy.copy(HTTP_HEADERS)
  headers['Content-Length'] = str(len(html))
  if extra_headers:
    headers.update(extra_headers)

  resp = u"""HTTP/1.1 200 OK\r
%s\r
\r
%s""" % ('\r\n'.join('%s: %s' % h for h in headers.items()), html)

  return (WARC_RESPONSE % (len(resp), url)) + '\r\n' + resp


def warc_record(record_str):
  split = record_str.split('\r\n\r\n', 1)
  headers = dict(header.split(': ', 1) for header in split[0].splitlines()
                 if ': ' in header)
  body = split[1] if len(split) == 2 else None
  return warc.WARCRecord(payload=body, headers=headers)

WARC_HEADER_RECORD = warc_record(WARC_HEADER)
WARC_METADATA_RECORD = warc_record(WARC_METADATA)
WARC_REQUEST_RECORD = warc_record(WARC_REQUEST)

WARC_FILE = '\r\n\r\n'.join(
  [WARC_HEADER, WARC_REQUEST, warc_response('foo', 'http://foo'), WARC_METADATA, ''])


class WarcToBigQueryTest(unittest.TestCase):
  maxDiff = None

  def test_convert_responses(self):
    foo_record = warc_record(warc_response('foo', 'http://foo'))
    bar_record = warc_record(warc_response('bar', 'http://bar',
                                           extra_headers={'Bar': 'Baz'}))
    bar_json = copy.deepcopy(BIGQUERY_JSON)
    bar_json.update({
      'url': 'http://bar',
      'html': HTML % ('', 'bar'),
      'headers': sorted(bar_json['headers'] + [['Bar', 'Baz']])
    })

    responses = [
      WARC_HEADER_RECORD,
      foo_record,
      WARC_METADATA_RECORD,
      bar_record,
      WARC_REQUEST_RECORD,
    ]
    self.assertEqual([BIGQUERY_JSON, bar_json],
                     list(warc_to_bigquery.convert_responses(responses)))

  def test_links(self):
    record = warc_record(warc_response("""\
foo <a href="#frag"></a>
bar <a class="x" rel="a b" href="/local">bar</a>
baz <a class="y u-in-reply-to" href="http://ext/ernal">baz</a>
baj <a class="u-repost-of z" href="http://ext/ernal"><img src="/baj"></a>
baj <link rel="c" class="w" href="http://link/tag" />
""", 'http://foo', html_head='<link rel="d e" href="https://head/link">'))

    self.assertEqual([
      ('https://head/link', '', 'link', ['d', 'e'], []),
      ('http://link/tag', '', 'link', ['c'], ['w']),
      ('#frag', '', 'a', [], []),
      ('/local', 'bar', 'a', ['a', 'b'], ['x']),
      ('http://ext/ernal', 'baz', 'a', [], ['y', 'u-in-reply-to']),
      ('http://ext/ernal', '<img src="/baj"/>', 'a', [], ['u-repost-of', 'z']),
    ], list(warc_to_bigquery.convert_responses([record]))[0]['links'])

  def test_microformats(self):
    for content, expected in (
        ('', []),
        ('foo', []),
        ('<div class="h-entry"></div>', ['h-entry']),
        ('<div class="h-entry">1</div> <div class="h-entry">2</div>', ['h-entry']),
        ('<div class="h-entry h-card"></div>', ['h-card', 'h-entry']),
        ('<div class="h-feed"><div class="h-entry"><div class="h-card">'
         '</div></div></div> <div class="h-adr"></div>',
         ['h-adr', 'h-card', 'h-entry', 'h-feed']),
        # microformats1 backward compatibility
        ('<div class="hentry"></div>', ['h-entry']),
    ):
      record = warc_record(warc_response(content, 'http://foo'))
      actual = list(warc_to_bigquery.convert_responses([record]))[0]\
                        ['mf2_classes']
      self.assertEqual(expected, actual, '%s %s %s' % (expected, actual, content))

  def test_rels(self):
    for content, expected in (
        ('', {}),
        ('<link rel="foo" href="http://x">',
         {'foo': ['http://x']}),
        ('<link rel="foo bar" href="http://x">',
         {'bar': ['http://x'], 'foo': ['http://x']}),
        ('<link rel="foo" href="http://x"> <link rel="bar foo" href="http://y">',
         {'bar': ['http://y'], 'foo': ['http://x', 'http://y']}),
    ):
      record = warc_record(warc_response(content, 'http://foo'))
      actual = list(warc_to_bigquery.convert_responses([record]))[0]['rels']
      self.assertEqual(expected, actual, '%s %s %s' % (expected, actual, content))

  def test_u_urls(self):
    for content, expected in (
        ('', []),
        ('foo', []),
        ('<div class="h-entry"></div>', []),
        ('<div class="h-entry"><a class="u-url" href="http://foo" /></div>',
         ['http://foo']),
        ('<div class="h-entry"><a class="u-url" href="http://foo" /></div>'
         '<div class="h-entry"><a class="u-url" href="http://bar" /></div>',
         ['http://foo', 'http://bar']),
        ('<div class="h-feed"><div class="h-entry">'
         '<a class="u-url" href="http://foo" /></div></div>',
         []),
        # microformats1 backward compatibility
        # http://microformats.org/wiki/rel-bookmark#rel.3D.22bookmark.22
        ('<div class="hentry"><a rel="bookmark" href="http://baz" /></div>',
         ['http://baz']),
    ):
      record = warc_record(warc_response(content, 'http://foo'))
      actual = list(warc_to_bigquery.convert_responses([record]))[0]['u_urls']
      self.assertEqual(expected, actual, '%s %s %s' % (expected, actual, content))

  def test_url_blacklist(self):
    records = [warc_record(warc_response('', 'http://foo%s' % path)) for path in (
        '/foo/bar?shared=email&x',
        '/?share=facebook',
        '/?x&share=tumblr',
        '/?like_comment=123',
        '/?x&replytocom=456',
        '/wp-login.php?redirect_to=qwert',
    )]
    self.assertEqual([], list(warc_to_bigquery.convert_responses(records)))

  def test_main(self):
    warc_path = '/tmp/test_warc_to_bigquery.warc.gz'
    with gzip.open(warc_path, 'wb') as f:
      f.write(WARC_FILE)

    warc_to_bigquery.main([warc_path])

    with gzip.open(warc_path.replace('warc.gz', 'json.gz')) as f:
      self.assertEqual([BIGQUERY_JSON], json.loads(f.read()))
