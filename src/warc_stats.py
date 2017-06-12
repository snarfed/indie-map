#!/usr/bin/env python3
"""Sums up statistics for a set of WARC files.

Usage: warc_stats.py site.warc.gz ...

Writes to stdout.

* total WARC file size (compressed, uncompressed)

* records
* requests
* responses
* URLs (request and response):
  * host
  * pay level domain
  * TLD
* HTTP status code
* HTTP version

WARC file format:
http://bibnum.bnf.fr/WARC/
http://warc.readthedocs.io/
"""
from collections import Counter
import gzip
import operator
import sys
from urllib.parse import urlparse

import warcio

# these map values to counts
rec_types = Counter()
sizes = Counter()  # by record type
hosts = Counter()
domains = Counter()
tlds = Counter()
content_types = Counter()


def main(warc_files):
  for in_filename in warc_files:
      print(in_filename, end='', flush=True)
      with gzip.open(in_filename, 'rb') as input:
          for i, record in enumerate(warcio.ArchiveIterator(input)):
              if i and i % 1000 == 0:
                  print('.', end='', flush=True)

              rec_types[record.rec_type] += 1
              sizes[record.rec_type] += record.rec_headers.total_len + record.length
              url = record.rec_headers.get('WARC-Target-URI')
              if record.rec_type == 'response' and url:
                  host = urlparse(url).netloc.split(':')[0]
                  hosts[host] += 1
                  domains['.'.join(host.rsplit('.', 2)[-2:])] += 1
                  tlds[host.split('.')[-1]] += 1
              if record.http_headers:
                  content_type = record.http_headers.get('Content-Type')
                  if content_type:
                      content_types[content_type.lower()] += 1
      print()

  for var in 'rec_types', 'sizes', 'hosts', 'domains', 'tlds', 'content_types':
      counter = globals()[var]
      print()
      print('%s %s' % (sum(counter.values()), var))
      for item in sorted(counter.items(), key=operator.itemgetter(1), reverse=True):
        print('%s %s' % item)



if __name__ == '__main__':
  main(sys.argv[1:])
