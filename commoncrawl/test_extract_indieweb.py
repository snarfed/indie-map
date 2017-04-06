# coding=utf-8
"""Unit tests for extract_indieweb.py.
"""
import base64
import cStringIO
import gzip
import os
import unittest

import boto
import moto
import mrjob.runner
import warc

import extract_indieweb

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
WARC-Target-URI: http://%s/photos/?gallery=Chorin%%202010-10&photo=119&exif_style=&show_thumbs=\r
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


def warc_response(body, domain='0pointer.de'):
  html = HTML % body
  headers = HTTP_HEADERS % len(html)
  resp = headers + '\r\n' + html
  return (WARC_RESPONSE % (len(resp), domain)) + '\r\n' + resp


@moto.mock_s3
class ExtractIndiewebTest(unittest.TestCase):
  maxDiff = None

  def setUp(self):
    super(ExtractIndiewebTest, self).setUp()
    self.mrjob = extract_indieweb.ExtractIndieweb().sandbox()
    self.mrjob.options.runner = 'hadoop'
    self.runner = self.mrjob.make_runner()

  @classmethod
  def s3_file(cls, bucket, key, contents):
    if os.path.splitext(key)[-1] == '.gz':
      buf = cStringIO.StringIO()
      with gzip.GzipFile(fileobj=buf, mode='wb') as f:
        f.write(contents)
      contents = buf.getvalue()

    conn = boto.connect_s3()
    bucket = conn.lookup(bucket) or conn.create_bucket(bucket)
    bucket.new_key(key).set_contents_from_string(contents)

  def assert_map(self, expected, responses, **kwargs):
    self.s3_file('commoncrawl', 'input.warc.gz', '\r\n\r\n'.join(
      [WARC_HEADER, WARC_REQUEST] +
      [warc_response(resp, **kwargs) for resp in responses] +
      [WARC_METADATA, '']))

    actual = list(self.mrjob.mapper('', 'input.warc.gz'))
    self.assertEqual(len(expected), len(actual), actual)
    for (exp_key, exp_val), (act_key, act_val) in zip(expected, actual):
      self.assertEqual(exp_key, act_key)
      self.assertMultiLineEqual(warc_response(exp_val),
                                base64.b64decode(act_val).strip())

  def test_mapper_no_mf2(self):
    self.assert_map([], ('foo',))

  def test_mapper_mf2(self):
    html = '<div class="h-entry">foo bar</div>'
    self.assert_map([('0pointer.de', html)], [html])

  def test_blacklist(self):
    self.assert_map([], '<div class="h-entry">foo bar</div>', domain='google.com')
    self.assertIn('reporter:counter:blacklist,google.com,1',
                  self.mrjob.stderr.getvalue().splitlines())
