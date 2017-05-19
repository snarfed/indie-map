#!/usr/bin/env python3
"""Generates a JSON file with Site records for each domain read from stdin.

See README.md for the Site table's schema.

BigQuery JSON format:
https://cloud.google.com/bigquery/data-formats#json_format
https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types
https://cloud.google.com/bigquery/loading-data#loading_nested_and_repeated_json_data
"""
import collections
import datetime
import json
import re
import sys
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import mf2py
import mf2util
import requests


class OrderedSet(collections.OrderedDict):
    def add(self, item):
        self[item] = None

    def update(self, iter):
        for item in iter:
            self.add(item)


def main():
    with open('sites.json') as out:
        for line in sys.stdin:
            domain = line.strip()
            print(domain, flush=True)
            json.dump(generate(domain), ensure_ascii=False)
            print(file=out)


def convert(domain):
    resp = requests.get('http://' + domain)
    fetch_time = datetime.datetime.now()
    soup = BeautifulSoup(resp.text, 'lxml')

    # extract these from:
    # * mf2 representative h-card
    # * HTML head and meta tags
    # * Open Graph tags, http://ogp.me/
    # * Clearbit's Enrichment and Logo APIs, by hand
    #   https://dashboard.clearbit.com/docs
    urls = OrderedSet()
    names = OrderedSet()
    descriptions = OrderedSet()
    pictures = OrderedSet()

    mf2 = mf2py.parse(url=resp.url, doc=soup)
    hcard = mf2util.representative_hcard(mf2, resp.url)
    if hcard:
        props = hcard.get('properties', {})
        names.update(props.get('name', []))
        urls.update(props.get('url', []))
        pictures.update(props.get('photo', []))
        for prop in 'note', 'label', 'description':
            descriptions.update(props.get(prop, []))

    # head/meta
    rels = mf2.get('rels', {})
    urls.update(rels.get('canonical', []))
    title = soup.title
    if title:
        names.add(title.string)
    meta_descs = soup.find_all('meta', attrs={'name': 'description'})
    descriptions.update(tag['content'] for tag in meta_descs)
    pictures.update(rels.get('icon', []))

    # OGP
    og_url = soup.find('meta', property='og:url')
    if og_url:
        urls.add(og_url['content'])
    og_desc = soup.find('meta', property='og:description')
    if og_desc:
        descriptions.add(og_desc['content'])
    names.update(tag['content'] for tag in soup.find_all(
        'meta', property=('og:title', 'og:site_name')))
    pictures.update(tag['content'] for tag in soup.find_all(
        'meta', property=('og:image', 'og:image:url', 'og:image:secure_url')))

    # Clearbit:
    # https://dashboard.clearbit.com/docs#enrichment-api
    # https://logo.clearbit.com/snarfed.org
    # https://person.clearbit.com/v2/combined/find?domain=snarfed.org
    #   (needs account and oauth token)

    if not urls:
        urls = [u'http://{}/'.format(domain)]
    if not names:
        names = [domain]

    return {
        'domain': domain,
        'urls': list(urls),
        'names': list(names),
        'descriptions': list(descriptions),
        'pictures': list(pictures),
        'hcard': json.dumps(hcard, sort_keys=True),
        'mf2': json.dumps(mf2, sort_keys=True),
        'rel_mes': rels.get('me', []),
        'html': resp.text,
        'fetch_time': fetch_time.isoformat('T'),
    }


if __name__ == '__main__':
  main()
