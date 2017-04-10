import gzip
import os.path as Path
#
import boto
import warc
#
from boto.s3.key import Key
from gzipstream import GzipStreamFile
from mrjob.job import MRJob


class CCJob(MRJob):
  def configure_options(self):
    super(CCJob, self).configure_options()
    self.pass_through_option('--runner')
    self.pass_through_option('-r')

  def process_record(self, record):
    """
    Override process_record with your mapper
    """
    raise NotImplementedError('Process record needs to be customized')

  def mapper(self, _, line):
    f = None
    ## If we're on EC2 or running on a Hadoop cluster, pull files via S3
    if self.options.runner in ['emr', 'hadoop']:
      # Connect to Amazon S3 using anonymous credentials
      conn = boto.connect_s3(anon=True, host='s3.amazonaws.com')
      pds = conn.get_bucket('commoncrawl')
      # Start a connection to one of the WARC files
      k = Key(pds, line)
      f = warc.WARCFile(fileobj=GzipStreamFile(k))
    ## If we're local, use files on the local file system
    else:
      line = Path.join(Path.abspath(Path.dirname(__file__)), line)
      # print 'Loading local file {}'.format(line)
      f = warc.WARCFile(fileobj=gzip.open(line))
    ###
    for i, record in enumerate(f):
      for key, value in self.process_record(record):
        yield key, value
      self.increment_counter('commoncrawl', 'processed_records', 1)

  def combiner(self, key, value):
    # use the reducer by default
    for key_val in self.reducer(key, value):
        yield key_val

  def reducer(self, key, value):
    yield key, sum(value)

"""MRJob over the Common Crawl WARC dataset that extracts IndieWeb pages.

We consider a page part of the IndieWeb if it has a microformats2 class or
advertizes a webmention or micropub endpoint.

http://commoncrawl.org/
https://github.com/commoncrawl/cc-mrjob
https://pythonhosted.org/mrjob/

https://indieweb.org/
http://microformats.org/wiki/microformats2
https://webmention.net/
https://micropub.net/
"""
import base64
from cStringIO import StringIO
import gzip
import os
import re
import sys
import urlparse

import boto
from mrjob.protocol import RawProtocol,  RawValueProtocol
from oauth_dropins.webutil import util
import warc

# from mrcc import CCJob


ENDPOINT_RE_STR = r"""rel=["']?(http://)?(webmention|micropub)(\.(net|org)/?)?["']?"""
ENDPOINT_RE = re.compile(ENDPOINT_RE_STR)

# note that mf2 class names are case sensitive
# http://microformats.org/wiki/parsing-microformats#Parsing_class_values
#
# (also note that this will find false positives when it matches text outside an
# HTML tag.
#
# mf2 h- vocabularies extracted from:
# http://microformats.org/wiki/h-entry#Core_Properties
MF2_CLASSES = ('adr', 'card', 'entry', 'event', 'feed', 'geo', 'item', 'listing', 'product', 'recipe', 'resume', 'review', 'review-aggregate')

INDIEWEB_RE = re.compile(r"""
class\s*=\s*["'][^"']*\bh-(%s)\b[^"']*["']
  |
%s
""" % ('|'.join(MF2_CLASSES), ENDPOINT_RE_STR), re.VERBOSE | re.UNICODE)

USE_BLACKLIST = False
if USE_BLACKLIST:
  with open('domain_blacklist.txt') as f:
    DOMAIN_BLACKLIST = util.load_file_lines(f)

S3_OUTPUT_BUCKET = 'indie-map'
# S3_OUTPUT_PREFIX = 'extracted'
s3_bucket = None  # global; initialized in reducer


class ExtractIndieweb(CCJob):
  INTERNAL_PROTOCOL = RawProtocol
  OUTPUT_PROTOCOL = RawProtocol

  def process_record(self, record):
    if record['WARC-Type'] != 'response':
      return

    domain = urlparse.urlparse(record['WARC-Target-URI']).netloc.lower()
    if USE_BLACKLIST and util.domain_or_parent_in(domain, DOMAIN_BLACKLIST):
      self.increment_counter('blacklist', domain, 1)
      return

    # The HTTP response is defined by a specification: first part is headers
    # (metadata) and then following two CRLFs (newlines) has the response
    payload = record.payload.read()

    http_headers, body = payload.split('\r\n\r\n', 1)
    if 'Content-Type: text/html' in http_headers and body.strip():
      if ENDPOINT_RE.search(http_headers) or INDIEWEB_RE.search(body):
        warcstr = StringIO()
        warcfile = warc.WARCFile(fileobj=warcstr, mode='w')
        warcfile.write_record(warc.WARCRecord(payload=payload, header=record.header))
        warcbuf = base64.b64encode(warcstr.getvalue())
        warcfile.close()

        # domain = headers['Host']
        yield domain, warcbuf

  def combiner(self, key, values):
    yield key, base64.b64encode(''.join(base64.b64decode(v) for v in values
                                        if v and v.strip()))

  def reducer(self, key, values):
    # combine and gzip records
    buf = StringIO()
    with gzip.GzipFile(fileobj=buf, mode='wb') as f:
      for value in values:
        f.write(base64.b64decode(value) + '\r\n\r\n')
    contents = buf.getvalue()

    filename = '%s.warc.gz' % key
    if self.options.runner in ('emr', 'hadoop'):
      # write to S3
      global s3_bucket
      if s3_bucket is None:
        s3_bucket = boto.connect_s3(host='s3-us-west-2.amazonaws.com').get_bucket(S3_OUTPUT_BUCKET)
      key = s3_bucket.new_key(os.path.join('extracted', filename))
      key.set_contents_from_string(contents)
    else:
      # write to local file
      with open(os.path.join('/tmp', filename), 'w') as f:
        f.write(contents)


if __name__ == '__main__':
  ExtractIndieweb.run()
