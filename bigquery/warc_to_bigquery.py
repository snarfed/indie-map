#!/usr/bin/env python3
"""Converts a WARC file to JSON Page records to be loaded into BigQuery.

See README.md for the Page table's schema.

WARC file format:
http://bibnum.bnf.fr/WARC/
http://warc.readthedocs.io/

BigQuery JSON format:
https://cloud.google.com/bigquery/data-formats#json_format
https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types
https://cloud.google.com/bigquery/loading-data#loading_nested_and_repeated_json_data
"""
import gzip
import json
import os
import re
import sys
from urllib.parse import urlparse

from bs4 import BeautifulSoup, UnicodeDammit
import mf2py
# import simplejson as json
import warcio

# known WordPress URL query params that redirect back to the current page or to
# silos, from e.g. the ShareDaddy plugin.
URL_BLACKLIST_RE = re.compile(r"""
  [?&]
    (shared?=(email|facebook|google-plus-1|linkedin|pinterest|pocket|reddit|skype|telegram|tumblr|twitter|youtube) |
    like_comment= |
    replytocom= |
    redirect_to= ) |
  ^https://waterpigs\.co\.uk/mentions/webmention/\?wmtoken= |
  /index\.php\?title= |
  ^https?://indieweb\.org/irc/([^/]+/)?....-..-../line/[0-9]+ |
  ^https?://chat\.indieweb\.org/([^/]+/)?....-..-../[0-9]+
  """, re.VERBOSE)
  # /search?... TODO based on www.ogok


def main(warc_files):
  for in_filename in warc_files:
    print(in_filename, end='', flush=True)
    assert in_filename.endswith('.warc.gz')
    out_filename = in_filename[:-len('.warc.gz')] + '.json.gz'

    # if os.path.exists(out_filename):
    #   print(' ...skipping, %s already exists.' % out_filename)
    #   continue

    with gzip.open(in_filename, 'rb') as input, \
         gzip.open(out_filename, 'wt', encoding='utf-8') as output:
      for i, record in enumerate(warcio.ArchiveIterator(input)):
        if i and i % 100 == 0:
          print('.', end='', flush=True)
          break
        row = maybe_convert(record)
        if row:
          # BigQuery JSON format is oddly specific: one object per line.
          json.dump(row, output, ensure_ascii=True)#encoding='utf-8')
          print(file=output)

    print(flush=True)

  print('Done.')


def maybe_convert(record):
  if record.rec_type != 'response':
    return

  if (record.http_headers.get_statuscode() != '200' or
      not record.http_headers.get('Content-Type', '').startswith('text/html')):
    return

  url = record.rec_headers.get('WARC-Target-URI')
  if URL_BLACKLIST_RE.search(url):
    return

  # TODO: charset from HTTP header Content-Type
  #
  # use UnicodeDammit to gracefully handle response contents with invalid
  # content for their character encoding, e.g. invalid start or continuation
  # bytes in UTF-8.
  body = UnicodeDammit(record.content_stream().read()).unicode_markup
  if not body:
    return

  soup = BeautifulSoup(body, 'lxml')

  links = [{
    'tag': link.name,
    'url': link['href'],
    'inner_html': ''.join(str(c) for c in link.children),  # inner HTML content
    'rels': link.get('rel', []),
    'classes': link.get('class', []),
  } for link in soup.find_all('link') + soup.find_all('a')
    if link.get('href')]

  mf2 = mf2py.parse(url=url, doc=soup)

  def mf2_classes(obj):
    if isinstance(obj, (list, tuple)):
      return sum((mf2_classes(elem) for elem in obj), [])
    elif isinstance(obj, dict):
      items = obj.get('items') or obj.get('children') or []
      return obj.get('type', []) + mf2_classes(items)
    raise RuntimeError('unexpected type: %r' % obj)

  return {
    'url': url,
    'domain': urlparse(url).netloc,
    'time': record.rec_headers.get('WARC-Date'),
    'headers': [{'name': name, 'value': value}
                for name, value in sorted(record.http_headers.headers)],
    'html': body,
    'links': links,
    'mf2': json.dumps(mf2),
    'mf2_classes': sorted(set(mf2_classes(mf2))),
    'rels': [{'value': val, 'urls': urls} for val, urls in
             mf2.get('rels', {}).items()],
    'u_urls': sum((item.get('properties', {}).get('url', [])
                   for item in (mf2.get('items', []))), []),
  }


if __name__ == '__main__':
  main(sys.argv[1:])
