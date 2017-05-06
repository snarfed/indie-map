#!/usr/bin/env python
"""Converts a WARC file to JSON to be loaded into BigQuery.

WARC file format:
http://bibnum.bnf.fr/WARC/
http://warc.readthedocs.io/

BigQuery JSON format:
https://cloud.google.com/bigquery/data-formats#json_format
https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types
https://cloud.google.com/bigquery/loading-data#loading_nested_and_repeated_json_data
"""
import gzip
import re
import sys
import urlparse

import bs4
import mf2py
import simplejson as json
import warc

# known WordPress URL query params that redirect back to the current page or to
# silos, from e.g. the ShareDaddy plugin.
URL_BLACKLIST_RE = re.compile(r"""
  [?&]
    (shared?=(email|facebook|google-plus-1|linkedin|pinterest|pocket|reddit|skype|telegram|tumblr|twitter|youtube) |
    like_comment= |
    replytocom= |
    redirect_to= ) |
  ^https://waterpigs\.co\.uk/mentions/webmention/\?wmtoken= |
  /index.php?title=
  """, re.VERBOSE)


def main(warc_files):
  for in_filename in warc_files:
    print in_filename
    assert in_filename.endswith('.warc.gz')
    out_filename = in_filename[:-len('.warc.gz')] + '.json.gz'
    input = warc.open(in_filename)
    with gzip.open(out_filename, 'wb') as output:
      json.dump(convert_responses(input), output, iterable_as_array=True,
                ensure_ascii=False, encoding='utf-8', indent=2)
      # for out in convert_responses(input):
        # pass
    input.close()


def convert_responses(records):
  for i, record in enumerate(records):
    # print >> sys.stderr, 'starting',
    if i and i % 1000 == 0:
      print '  %s' % i

    if record['WARC-Type'] != 'response':
      continue

    # payload is HTTP headers, then two CRLFs, then response body
    payload = record.payload
    if not isinstance(payload, basestring):
      payload = payload.read()

    split = payload.split('\r\n\r\n', 1)
    if len(split) != 2:
      # print 'nope: no payload'
      continue

    http_headers, body = split
    http_headers_lines = http_headers.splitlines()
    body = body.strip()
    if (http_headers_lines[0] not in ('HTTP/1.0 200 OK', 'HTTP/1.1 200 OK') or
        'Content-Type: text/html' not in http_headers or
        not body):
      # print 'nope:\n%s' % http_headers
      continue

    url = record['WARC-Target-URI']
    if URL_BLACKLIST_RE.search(url):
      # print 'nope: blacklist'
      continue

    # print >> sys.stderr, '%s...' % url,
    soup = bs4.BeautifulSoup(body, 'lxml')

    links = [(
      link['href'],
      ''.join(unicode(c) for c in link.children),  # inner HTML content
      link.name,
      link.get('rel', []),
      link.get('class', []),
    ) for link in soup.find_all('link') + soup.find_all('a')
      if link.get('href')]

    mf2 = mf2py.parse(url=url, doc=soup)

    def mf2_classes(obj):
      if isinstance(obj, (list, tuple)):
        return sum((mf2_classes(elem) for elem in obj), [])
      elif isinstance(obj, dict):
        items = obj.get('items') or obj.get('children') or []
        return obj.get('type', []) + mf2_classes(items)
      raise RuntimeError('unexpected type: %r' % obj)

    # print >> sys.stderr, 'done.',
    yield {
      'url': url,
      'domain': urlparse.urlparse(url).netloc,
      'time': record['WARC-Date'],
      'headers': [list(h.split(': ', 1)) for h in sorted(http_headers_lines[1:])],
      'html': body,
      'links': links,
      'mf2': json.dumps(mf2, ensure_ascii=False, encoding='utf-8'),
      'mf2_classes': sorted(set(mf2_classes(mf2))),
      'rels': mf2.get('rels'),
      'u_urls': sum((item.get('properties', {}).get('url', [])
                     for item in (mf2.get('items', []))), []),
    }
    # print >> sys.stderr, 'next!'


if __name__ == '__main__':
  main(sys.argv[1:])
