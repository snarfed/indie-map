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

import bs4
import mf2py
import mf2util
import requests


class FieldSet(collections.OrderedDict):
    def add(self, item):
        if item:
            if isinstance(item, bs4.element.Tag):
                item = item.string
            self[item] = None

    def update(self, iter):
        for item in iter:
            self.add(item)

    def add_metas(self, soup, **kwargs):
        self.update(tag['content'] for tag in soup.find_all('meta', **kwargs))


def main():
    for line in sys.stdin:
        domain = line.strip()
        print(domain, file=sys.stderr)
        out = generate(domain)
        if out:
            json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


def get_texts(obj, property):
    """Returns plain text string values from a property of an mf2 object."""
    return [(val.get('value') if isinstance(val, dict) else val).strip()
            for val in obj.get('properties', {}).get(property, [])]


def generate(domain):
    try:
        resp = requests.get('http://' + domain)
        resp.raise_for_status()
    except Exception as e:
        print(str(e), file=sys.stderr)
        return

    fetch_time = datetime.datetime.now()
    soup = bs4.BeautifulSoup(resp.text, 'lxml')

    # extract these from:
    # * mf2 representative h-card
    # * HTML head and meta tags
    # * Open Graph tags
    # * Twitter card tags
    # * Clearbit's Enrichment and Logo APIs
    urls = FieldSet()
    names = FieldSet()
    descriptions = FieldSet()
    pictures = FieldSet()

    mf2 = mf2py.parse(url=resp.url, doc=soup)
    hcard = mf2util.representative_hcard(mf2, resp.url)
    if hcard:
        names.update(get_texts(hcard, 'name'))
        urls.update(get_texts(hcard, 'url'))
        pictures.update(get_texts(hcard, 'photo'))
        for prop in 'note', 'label', 'description':
            descriptions.update(get_texts(hcard, prop))

    # HTML head/meta tags
    rels = mf2.get('rels', {})
    urls.update(rels.get('canonical', []))
    names.add(soup.title)
    descriptions.add_metas(soup, attrs={'name': 'description'})
    pictures.update(rels.get('icon', []))

    # Open Graph tags, http://ogp.me/
    urls.add_metas(soup, property='og:url')
    descriptions.add_metas(soup, property='og:description')
    names.add_metas(soup, property=('og:title', 'og:site_name'))
    pictures.add_metas(
        soup, property=('og:image', 'og:image:url', 'og:image:secure_url'))

    # Twitter card tags, https://dev.twitter.com/cards/overview
    urls.add_metas(soup, attrs={'name': 'twitter:url'})
    names.add_metas(soup, attrs={'name': 'twitter:title'})
    descriptions.add_metas(soup, attrs={'name': 'twitter:description'})
    pictures.add_metas(soup, attrs={'name': 'twitter:image'})

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
        'fetch_time': fetch_time.isoformat('T'),
        'urls': list(urls),
        'names': list(names),
        'descriptions': list(descriptions),
        'pictures': list(pictures),
        'hcard': json.dumps(hcard, sort_keys=True),
        'rel_mes': rels.get('me', []),
        'mf2': json.dumps(mf2, sort_keys=True),
        'html': resp.text,
    }


if __name__ == '__main__':
  main()
