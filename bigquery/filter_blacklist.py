#!/usr/bin/env python3
"""Reads a WARC file, discards blacklisted URL records, and writes the result.
"""
import gzip
import os
import sys

import warcio

import blacklist


for path in sys.argv[1:]:
    assert path.endswith('.warc.gz')
    out = path.replace('.warc.gz', '.warc.filtered.gz')

    with gzip.open(path, 'rb') as input, open(out, 'wb') as output:
        writer = warcio.WARCWriter(filebuf=output, gzip=True)
        for i, record in enumerate(warcio.ArchiveIterator(input)):
            url = record.rec_headers.get('WARC-Target-URI')
            # print('%s %s' % (record.rec_type, url))
            if url:
                if url.startswith('<') and url.endswith('>'):
                    url = url[1:-1]
                if blacklist.URL_BLACKLIST_RE.search(url):
                    continue
            writer.write_record(record)
            if i and i % 1000 == 0:
                break
