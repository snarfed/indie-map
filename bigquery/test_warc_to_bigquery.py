# coding=utf-8
"""Unit tests for warc_to_bigquery.py.
"""
import copy
from cStringIO import StringIO
import json
import os
import unittest

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

EMPTY_MF2 = json.dumps({'items': [], 'rel-urls': {}, 'rels': {}}, indent=2)


class WarcToBigQueryTest(unittest.TestCase):
  maxDiff = None

  def test_convert_responses(self):
    foo_html = HTML % ('', 'foo')
    foo_record = warc_record(warc_response('foo', 'http://foo'))
    foo_headers = copy.copy(HTTP_HEADERS.items())
    foo_headers.append(('Content-Length', str(len(foo_html))))

    bar_record = warc_record(warc_response('bar', 'http://bar',
                                           extra_headers={'Bar': 'Baz'}))
    bar_headers = copy.copy(foo_headers)
    bar_headers.append(('Bar', 'Baz'))

    self.assertEqual([{
      'url': 'http://foo',
      'time': '2014-08-20T06:36:13Z',
      'http_response_headers': sorted(foo_headers),
      'html': foo_html,
      'mf2': EMPTY_MF2,
      'mf2_classes': [],
      'links': [],
    }, {
      'url': 'http://bar',
      'time': '2014-08-20T06:36:13Z',
      'http_response_headers': sorted(bar_headers),
      'html': HTML % ('', 'bar'),
      'mf2': EMPTY_MF2,
      'mf2_classes': [],
      'links': [],
    }], list(warc_to_bigquery.convert_responses([
      WARC_HEADER_RECORD,
      foo_record,
      WARC_METADATA_RECORD,
      bar_record,
      WARC_REQUEST_RECORD,
    ])))

  def test_convert_responses_links(self):
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

  def test_convert_responses_microformats(self):
    for content, expected in (
        ('', []),
        ('foo', []),
        # ('<div class="hentry"></div>', ['hentry']),
        ('<div class="h-entry"></div>', ['h-entry']),
        ('<div class="h-entry">1</div> <div class="h-entry">2</div>', ['h-entry']),
        ('<div class="h-entry h-card"></div>', ['h-card', 'h-entry']),
        ('<div class="h-feed"><div class="h-entry"><div class="h-card">'
         '</div></div></div> <div class="h-adr"></div>',
         ['h-adr', 'h-card', 'h-entry', 'h-feed']),
    ):
      record = warc_record(warc_response(content, 'http://foo'))
      actual = list(warc_to_bigquery.convert_responses([record]))[0]\
                        ['mf2_classes']
      self.assertEqual(expected, actual, '%s %s %s' % (expected, actual, content))

  # def test_run(self):
  #   hcard = warc_response('<div class="h-card">one</div>')
  #   micropub = warc_response('two', header='Link: <http://mp>; rel="micropub"')

  #   with gzip.open('/tmp/input.warc.gz', 'wb') as f:
  #     f.write('\r\n\r\n'.join(
  #       [WARC_HEADER, WARC_REQUEST] +
  #       [hcard, warc_response('not indie web'), micropub] +
  #       [WARC_METADATA, '']))

  #   mrjob = self.mrjob.sandbox(stdin=StringIO('/tmp/input.warc.gz'))
  #   mrjob.options.runner = 'local'
  #   self.s3.create_bucket('indie-map')
  #   try:
  #     mrjob.run_job()
  #   except:
  #     print mrjob.stdout.getvalue(), mrjob.stderr.getvalue()
  #     raise

  #   with gzip.open('/tmp/0pointer.de.warc.gz') as f:
  #     self.assertMultiLineEqual(hcard + '\r\n\r\n' + micropub, f.read().strip())
