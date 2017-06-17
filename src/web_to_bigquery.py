#!/usr/bin/env python3
"""Generates a JSON file with sites records based on web full files.

Usage: web_to_bigquery.py DIR

DIR is the 'full' directory output by make_web.py. Writes to site.json output file.

Doesn't do much, just strips the links field and JSON-encodes the hcard field.
"""

import json
import os
import sys


def main(dir):
    with open('sites.json', 'wt', encoding='utf-8') as outfile:
        for filename in os.listdir(dir):
            with open(os.path.join(dir, filename), 'rt', encoding='utf-8') as infile:
                site = json.load(infile)
            site.pop('links', None)
            site['hcard'] = json.dumps(site['hcard'], ensure_ascii=False)
            json.dump(site, outfile, ensure_ascii=False)
            print(file=outfile)


if __name__ == '__main__':
  main(sys.argv[1])
