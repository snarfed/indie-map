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
import json
import re
import sys
import urlparse

import bs4
import mf2py
import warc


# mf2 h- vocabularies extracted from:
# http://microformats.org/wiki/h-entry#Core_Properties
#
# note that mf2 class names are case sensitive
# http://microformats.org/wiki/parsing-microformats#Parsing_class_values
MF2_CLASSES = frozenset('h-%s' % cls for cls in
  ('adr', 'card', 'entry', 'event', 'feed', 'geo', 'item', 'listing', 'product',
   'recipe', 'resume', 'review', 'review-aggregate'))

# mf1 h- vocabularies extracted from the specs linked to in:
# http://microformats.org/wiki/Main_Page#Classic_Microformats
#
# eg http://microformats.org/wiki/hatom, http://microformats.org/wiki/hcard, ...
#
# note that mf1 class names are case sensitive
# http://microformats.org/wiki/parsing-microformats#Parsing_class_values
MF1_CLASSES = frozenset((
  'hfeed', 'hentry', 'vcard', 'haudio', 'vcalendar', 'vevent', 'fn', 'hproduct',
  'hrecipe', 'hresume', 'hreview', 'hreview-aggregate', 'adr', 'geo',
))


def main(warc_files):
  for in_filename in warc_files:
    out_filename = re.sub('\.warc(\.gz)$', '', filename) + '.json.gz'
    with warc.open(in_filename) as input, gzip.open(out_filename, 'w') as output:
      json.dump(convert_responses(input), output)


def convert_responses(records):
  for record in records:
    if record['WARC-Type'] != 'response':
      continue

    # payload is HTTP headers, then two CRLFs, then response body
    payload = record.payload
    if not isinstance(payload, basestring):
      payload = payload.read()

    split = payload.split('\r\n\r\n', 1)
    if len(split) != 2:
      continue

    http_headers, body = split
    http_headers_lines = http_headers.splitlines()
    body = body.strip()
    if (http_headers_lines[0] not in ('HTTP/1.0 200 OK', 'HTTP/1.1 200 OK') or
        'Content-Type: text/html' not in http_headers or
        not body):
      continue

    url = record['WARC-Target-URI']

    soup = bs4.BeautifulSoup(body, 'lxml')

    links = [(
      link['href'],
      ''.join(unicode(c) for c in link.children),  # inner HTMl content
      link.name,
      link.get('rel', []),
      link.get('class', []),
    ) for link in soup.find_all('link') + soup.find_all('a')]

    mf2 = mf2py.parse(url=url, doc=soup)

    def mf2_classes(obj):
      if isinstance(obj, (list, tuple)):
        return sum((mf2_classes(elem) for elem in obj), [])
      elif isinstance(obj, dict):
        items = obj.get('items') or obj.get('children') or []
        return obj.get('type', []) + mf2_classes(items)
      raise RuntimeError('unexpected type: %r' % obj)

    yield {
      'url': url,
      'time': record['WARC-Date'],
      'http_response_headers': [tuple(h.split(': ', 1))
                                for h in sorted(http_headers_lines[1:])],
      'html': body,
      'links': links,
      'mf2': json.dumps(mf2, indent=2),
      'mf2_classes': sorted(set(mf2_classes(mf2))),
    }

# url blacklist! get from wget.sh

# mf2 properties...?
# rel-canonical
# u-url
# etc

if __name__ == '__main__':
  main(sys.argv[1:])
