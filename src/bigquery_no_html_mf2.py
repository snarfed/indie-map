#!/usr/bin/env python3
"""Removes the html and mf2 fields from BigQuery JSON 'page' files.

Usage: bigquery_no_html_mf2.py INPUT_DIR OUTPUT_DIR

INPUT_DIR is the 'full' directory output by make_web.py. Writes the same files
to OUTPUT_DIR.
"""

import gzip
import json
import os
import sys


def main(indir, outdir):
    for filename in os.listdir(indir):
        print(filename, end='', flush=True)
        with gzip.open(os.path.join(indir, filename), 'rt', encoding='utf-8') as infile, \
             gzip.open(os.path.join(outdir, filename), 'wt', encoding='utf-8') as outfile:
            for i, line in enumerate(infile):
                if i and i % 100 == 0:
                    print('.', end='', flush=True)
                page = json.loads(line)
                del page['html']
                del page['mf2']
                json.dump(page, outfile)
                print(file=outfile)  # newline
        print()


if __name__ == '__main__':
  main(*sys.argv[1:])
