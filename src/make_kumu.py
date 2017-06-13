#!/usr/bin/env python3
"""Generates CSV files for sites and connections to import into Kumu.

Usage: make_kumu.py [DIR]

Expects indie per-site JSON files in DIR, e.g. as created by make_web.py in
the indie/ directory.

Writes two output files to the current directory, kumu.elements.csv and
kumu.connections.csv.

Kumu import file format: https://docs.kumu.io/guides/import.html
"""
import csv
import json
import os
import sys

MF2_TO_TAG = {
    'in-reply-to': 'reply',
    'invitee': 'invite',
    'quotation-of': 'quotation',
    'repost-of': 'repost',
    'like-of': 'like',
    'favorite-of': 'favorite',
    'bookmark-of': 'bookmark',
    'other': 'other',
}


def make(sites, elems_file, conns_file):
    """Converts site JSON web objects to Kumu importable CSV files.

    Args:
      sites: JSON web objects created by make_web.py.
      elems_file, conns_fie: output file objects
    """
    elems = csv.DictWriter(elems_file, fieldnames=(
        'Label', 'URL', 'Title', 'Description', 'Tags', 'Image', 'LinksIn',
        'LinksOut', 'Pages', 'Server', 'Mf2Classes'))
    elems.writeheader()

    conns = csv.DictWriter(conns_file, fieldnames=(
        'From', 'To', 'Tags', 'Links', 'Strength'))
    conns.writeheader()

    def first(field):
        val = site.get(field)
        return val[0] if val else ''

    def pipe(field):
        return '|'.join(site.get(field) or [])

    for site in sites:
        elems.writerow({
            'Label': site['domain'],
            'URL': first('urls'),
            'Title': first('names'),
            'Description': '\n'.join((first('names'), first('descriptions'))).strip(),
            'Image': first('pictures'),
            'LinksIn': site['links_in'],
            'LinksOut': site['links_out'],
            'Pages': site.get('num_pages'),
            'Tags': pipe('tags'),
            'Server': pipe('servers'),
            'Mf2Classes': pipe('mf2_classes'),
        })

        for linked, data in site['links'].items():
            out = data.get('out', {})
            out_links = sum(out.values())
            if not out_links:
                continue
            conns.writerow({
                'From': site['domain'],
                'To': linked,
                'Tags': '|'.join(MF2_TO_TAG[cls] for cls in out.keys()),
                'Links': out_links,
                'Strength': data['score'],
            })


def sites():
    for i, filename in enumerate(os.listdir(sys.argv[1])):
        if i and i % 100 == 0:
            print('.', end='', flush=True)
        with open(os.path.join(sys.argv[1], filename), 'rt', encoding='utf-8') as f:
            yield json.load(f)


def main():
    with open('kumu.elements.csv', 'wt', encoding='utf-8') as elems_file, \
         open('kumu.connections.csv', 'wt', encoding='utf-8') as conns_file:
        make(sites(), elems_file, conns_file)


if __name__ == '__main__':
    main()
