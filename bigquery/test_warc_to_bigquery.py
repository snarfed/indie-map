# coding=utf-8
"""Unit tests for warc_to_bigquery.py.
"""
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
HTTP_HEADERS = """\
HTTP/1.1 200 OK\r
Date: Wed, 20 Aug 2014 06:36:13 GMT\r
Server: Apache\r
X-Powered-By: PHP/5.3.8-1+b1\r
Content-Length: %s\r
Connection: close\r
Content-Type: text/html; charset=utf-8\r
"""
HTML = """\
<!DOCTYPE html>
<html>
<head>
foo
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

def warc_response(body, url, extra_header=None):
  html = HTML % body
  headers = HTTP_HEADERS % len(html)
  if extra_header:
    headers += extra_header + '\r\n'
  resp = headers + '\r\n' + html
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
    self.assertEqual([{
      'url': 'http://foo',
      'time': '2014-08-20T06:36:13Z',
      'html': HTML % 'foo',
      'mf2': EMPTY_MF2,
    }, {
      'url': 'http://bar',
      'time': '2014-08-20T06:36:13Z',
      'html': HTML % 'bar',
      'mf2': EMPTY_MF2,
    }], list(warc_to_bigquery.convert_responses([
      WARC_HEADER_RECORD,
      warc_record(warc_response('foo', 'http://foo')),
      WARC_METADATA_RECORD,
      warc_record(warc_response('bar', 'http://bar')),
      WARC_REQUEST_RECORD,
    ])))

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
