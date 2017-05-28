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

TODO:
* upload more snippets!
"""
import gzip
import json
import os
import sys
from urllib.parse import urlparse

from bs4 import BeautifulSoup, UnicodeDammit
import mf2py
import warcio

import blacklist

# Size limit per row, in bytes. Docs say it's 2MB:
# https://cloud.google.com/bigquery/quota-policy#import
# ...but error message from empirical test on 5/28/2017 says 10MB:
# $ bq load ...
# - gs://indie-map/bigquery/...json.gz: JSON parsing error in
# row starting at position 1486770: . Row size is larger than: 10485760.
MAX_ROW_SIZE = 10 * 1024 * 1024  # 10MB
MAX_ROW_MESSAGE = '[OMITTED to keep BigQuery record under size limit]'


def main(warc_files):
  for in_filename in warc_files:
    print(in_filename, end='', flush=True)
    assert in_filename.endswith('.warc.gz')
    path_prefix = in_filename[:-len('.warc.gz')]
    out_filename = path_prefix + '.json.gz'
    domain = os.path.basename(path_prefix)

    if os.path.exists(out_filename):
      print(' ...skipping, %s already exists.' % out_filename)
      continue

    with gzip.open(in_filename, 'rb') as input, \
         gzip.open(out_filename, 'wt', encoding='utf-8') as output:
      for i, record in enumerate(warcio.ArchiveIterator(input)):
        if i and i % 100 == 0:
          print('.', end='', flush=True)
          # if i % 1000 == 0:
          #   break
        try:
          row = maybe_convert(record, domain)
          if row:
            # BigQuery JSON format is oddly specific: one object per line.
            # assert len(json.dumps(row, ensure_ascii=True)) <= MAX_ROW_SIZE
            json.dump(row, output, ensure_ascii=True)
            print(file=output)
        except:
          print('Failed on %s record %s (0-indexed)' % (in_filename, i),
                file=sys.stderr)
          raise

    print(flush=True)

  print('Done.')


def get_urls(objs):
  """Extracts string URLs from a list of either string URLs or mf2 dicts.

  Many mf2 properties can contain either string URLs or full mf2 objects, e.g.
  h-cites. in-reply-to is the most commonly used example:
  http://indiewebcamp.com/in-reply-to#How_to_consume_in-reply-to

  Stolen from granary/microformats2.py.

  Args:
    objs: sequence of either string URLs or embedded mf2 objects

  Returns:
    list of string URLs
  """
  urls = []

  for item in objs:
    if isinstance(item, str):
      urls.append(item)
    else:
      itemtype = [x for x in item.get('type', []) if x.startswith('h-')]
      if itemtype:
        item = item.get('properties') or item
        urls.extend(get_urls(item.get('url', [])))

  return urls


def maybe_convert(record, domain):
  """Converts a WARC record to JSON rows for the Page and Html tables.

  Arg:
    record: warcio.Record
    domain: string

  Returns:
    dict, JSON Page record, or None
  """
  if record.rec_type != 'response':
    return

  if (record.http_headers.get_statuscode() != '200' or
      not record.http_headers.get('Content-Type', '').startswith('text/html')):
    return

  url = record.rec_headers.get('WARC-Target-URI')
  if blacklist.URL_BLACKLIST_RE.search(url):
    return

  assert domain
  url_domain = urlparse(url).netloc.split(':')[0]
  if url_domain != domain and not url_domain.endswith('.' + domain):
    return

  # TODO: charset from HTTP header Content-Type
  #
  # use UnicodeDammit to gracefully handle response contents with invalid
  # content for their character encoding, e.g. invalid start or continuation
  # bytes in UTF-8.
  body_bytes = record.content_stream().read()
  body = UnicodeDammit(body_bytes).unicode_markup
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

  row = {
    'domain': url_domain,
    'url': url,
    'fetch_time': record.rec_headers.get('WARC-Date'),
    'links': links,
    'rels': [],  # placeholders so that key order is preserved
    'u_urls': [],
    'mf2_classes': [],
    'mf2': '{}',
    'headers': [{'name': name, 'value': value}
                for name, value in sorted(record.http_headers.headers)],
    # heuristic: check that HTML is <= 1/2 max size to avoid cost of serializing
    # this whole JSON object just to check its length.
    'html': body if len(body_bytes) <= MAX_ROW_SIZE / 2 else MAX_ROW_MESSAGE,
  }

  try:
    mf2 = mf2py.parse(url=url, doc=soup)
  except Exception as e:
    print('mf2py.parse with lxml failed on %s; switching to html5lib: %s' % (url, e))
    try:
      mf2 = mf2py.parse(url=url, doc=BeautifulSoup(body, 'html5lib'))
    except Exception as e2:
      print('mf2py.parse with html5lib failed too, giving up: %s' % e2)
      return row

  def mf2_classes(obj):
    if isinstance(obj, (list, tuple)):
      return sum((mf2_classes(elem) for elem in obj), [])
    elif isinstance(obj, dict):
      items = obj.get('items') or obj.get('children') or []
      return obj.get('type', []) + mf2_classes(items)
    raise RuntimeError('unexpected type: %r' % obj)

  row.update({
    'rels': [{'value': val, 'urls': urls} for val, urls in
             mf2.get('rels', {}).items()],
    'u_urls': get_urls(mf2.get('items', [])),
    'mf2_classes': sorted(set(mf2_classes(mf2))),
    'mf2': json.dumps(mf2 or {}),
  })
  return row


if __name__ == '__main__':
  main(sys.argv[1:])
