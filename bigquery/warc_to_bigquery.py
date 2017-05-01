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

# note that mf2 class names are case sensitive
# http://microformats.org/wiki/parsing-microformats#Parsing_class_values
#
# note that this will find false positives when it matches outside an HTML tag.
#
# mf2 h- vocabularies extracted from:
# http://microformats.org/wiki/h-entry#Core_Properties
MF2_CLASSES = ('adr', 'card', 'entry', 'event', 'feed', 'geo', 'item', 'listing', 'product', 'recipe', 'resume', 'review', 'review-aggregate')
MF2_RE = re.compile(r"""class\s*=\s*["'][^"']*\bh-(%s)\b[^"']*["']""" %
                    '|'.join(MF2_CLASSES))


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

    yield {
      'url': url,
      'time': record['WARC-Date'],
      'http_response_headers': [tuple(h.split(': ', 1))
                                for h in sorted(http_headers_lines[1:])],
      'html': body,
      'mf2': json.dumps(mf2py.parse(url=url, doc=soup), indent=2),
      'links': links,
    }

# links: array: string HTML tag (a or link), string target, array: string mf2 classes/rels, inner text or HTML
# mf2 properties...?
# rel-canonical
# u-url
# etc

if __name__ == '__main__':
  main(sys.argv[1:])
