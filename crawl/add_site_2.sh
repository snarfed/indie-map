#!/bin/bash
#
# Run to do the second half of adding new site(s). First half is add_site_1.sh.
#
# TODO: still in progress. need to s/$1/$@/ , add commas and quotes.
#
# Usage: add_site_2.sh DOMAIN...

set -x
set -e

# Social graph: links by mf2 (~50GB)
# Download: https://bigquery.cloud.google.com/table/indie-map:indiemap.links_social_graph
#
# Alternative: can try this for just the new domains (untested!)
# bq --format=prettyjson query > links.$1.json <<EOF
# SELECT * FROM indiemap.links_social_graph
# WHERE from_domain IN ($@) OR to_site IN ($@)
# EOF

# Sites: additional metadata: singular columns (~200GB)
# https://bigquery.cloud.google.com/savedquery/464705913036:23c4b0104dc24dff8371af71b3605a5f
bq --format=prettyjson query > site_extra_singular.$1.json <<EOF
SELECT
  domain,
  MIN(fetch_time) AS crawl_start,
  MAX(fetch_time) AS crawl_end,
  COUNT(*) AS num_pages,
  SUM(LENGTH(html)) as total_html_size,
  ARRAY_AGG(DISTINCT (SELECT REGEXP_REPLACE(value, '/[0-9.]+', '') FROM p.headers WHERE name = 'Server')
            IGNORE NULLS) AS servers,
  ARRAY_AGG(DISTINCT REGEXP_REPLACE(
      REGEXP_EXTRACT(
        -- find meta generator tags
        REGEXP_EXTRACT(html, '<meta[^>]* name="generator"[^>]*>'),
        -- extract content value
        'content *= *[\'"]([^\'"]+)'),
      -- drop version numbers
      '[ :]*[0-9.]{2,}', '')
    IGNORE NULLS) AS meta_generators
FROM indiemap.canonical_pages p
GROUP BY domain;
EOF

#  Sites: additional metadata: rels (~15GB)
# https://bigquery.cloud.google.com/savedquery/464705913036:2cf3275e38174a2a8f6a94811249af10
bq --format=prettyjson query > site_extra_rels.$1.json <<EOF
SELECT
  domain,
  STRUCT(
  ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value IN ('webmention', 'http://webmention.org/')
                  LIMIT 1) IGNORE NULLS), '') AS webmention,
  ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value IN ('micropub', 'http://micropub.net/')
                  LIMIT 1) IGNORE NULLS), '') AS micropub,
  ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value = 'authorization_endpoint'
                  LIMIT 1) IGNORE NULLS), '') AS authorization,
  ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value = 'token_endpoint'
                  LIMIT 1) IGNORE NULLS), '') AS token,
  ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value = 'hub'
                  LIMIT 1) IGNORE NULLS), '') AS websub,
  ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value = 'generator'
                  LIMIT 1) IGNORE NULLS), '') AS generator
  ) AS endpoints
FROM indiemap.canonical_pages p, p.rels r
GROUP BY domain;
EOF

#  Sites: additional metadata: mf2 classes (~15GB)
# https://bigquery.cloud.google.com/savedquery/464705913036:19a763c26f5440bdbcf2eeb12b806641
bq --format=prettyjson query > site_extra_mf2.$1.json <<EOF
SELECT domain, ARRAY_AGG(DISTINCT m IGNORE NULLS) AS mf2_classes
FROM indiemap.canonical_pages p, p.mf2_classes m
GROUP BY domain;
EOF


~/src/indie-map/src/make_web.py site.$1.json.gz links.$1.json site_extra*.$1.json

gsutil -m cp base/$1.json gs://www.indiemap.org/
gsutil -m cp indie/$1.json gs://www.indiemap.org/indie/
gsutil -m cp full/$1.json gs://www.indiemap.org/full/

~/src/indie-map/src/web_to_bigquery.py indie

~/src/indie-map/src/make_kumu.py indie
