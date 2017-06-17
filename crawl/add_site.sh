#!/bin/bash

set -x
set -e

~/src/indie-map/crawl/wget.sh $1

gsutil cp $1.warc.gz gs://indie-map/crawl/

source ~/src/indie-map/src/local/bin/activate
~/src/indie-map/src/warc_to_bigquery.py $1.warc.gz

gsutil cp $1.json.gz gs://indie-map/bigquery/
bq load --source_format=NEWLINE_DELIMITED_JSON indiemap.pages gs://indie-map/bigquery/$1.json.gz

echo $1 | ~/src/indie-map/src/sites_to_bigquery.py | gzip > site.$1.json.gz
# bq load --source_format=NEWLINE_DELIMITED_JSON indiemap.sites site.$1.json.gz


# # Social graph: links by mf2 (~50G)
# # https://bigquery.cloud.google.com/table/indie-map:indiemap.links_social_graph
# bq --format=prettyjson query > links.$1.json <<EOF
# SELECT * FROM indiemap.links_social_graph WHERE from_domain = $1 OR to_domain = $1
# EOF

# # Sites: additional metadata: singular columns (~200GB)
# # https://bigquery.cloud.google.com/savedquery/464705913036:23c4b0104dc24dff8371af71b3605a5f
# bq --format=prettyjson query > site_extra_singular.$1.json <<EOF
# SELECT
#   domain,
#   MIN(fetch_time) AS crawl_start,
#   MAX(fetch_time) AS crawl_end,
#   COUNT(*) AS num_pages,
#   SUM(LENGTH(html)) as total_html_size,
#   ARRAY_AGG(DISTINCT (SELECT REGEXP_REPLACE(value, '/[0-9.]+', '') FROM p.headers WHERE name = 'Server')
#             IGNORE NULLS) AS servers,
#   ARRAY_AGG(DISTINCT REGEXP_REPLACE(
#       REGEXP_EXTRACT(
#         -- find meta generator tags
#         REGEXP_EXTRACT(html, '<meta[^>]* name="generator"[^>]*>'),
#         -- extract content value
#         'content *= *[\'"]([^\'"]+)'),
#       -- drop version numbers
#       '[ :]*[0-9.]{2,}', '')
#     IGNORE NULLS) AS meta_generators
# FROM indiemap.canonical_pages p
# GROUP BY domain;
# EOF

# #  Sites: additional metadata: rels (~15G)
# # https://bigquery.cloud.google.com/savedquery/464705913036:2cf3275e38174a2a8f6a94811249af10
# bq --format=prettyjson query > site_extra_rels.$1.json <<EOF
# SELECT
#   domain,
#   STRUCT(
#   ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value IN ('webmention', 'http://webmention.org/')
#                   LIMIT 1) IGNORE NULLS), '') AS webmention,
#   ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value IN ('micropub', 'http://micropub.net/')
#                   LIMIT 1) IGNORE NULLS), '') AS micropub,
#   ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value = 'authorization_endpoint'
#                   LIMIT 1) IGNORE NULLS), '') AS authorization,
#   ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value = 'token_endpoint'
#                   LIMIT 1) IGNORE NULLS), '') AS token,
#   ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value = 'hub'
#                   LIMIT 1) IGNORE NULLS), '') AS websub,
#   ARRAY_TO_STRING(ARRAY_AGG(DISTINCT (SELECT u FROM r.urls u WHERE r.value = 'generator'
#                   LIMIT 1) IGNORE NULLS), '') AS generator
#   ) AS endpoints
# FROM indiemap.canonical_pages p, p.rels r
# GROUP BY domain;
# EOF

# #  Sites: additional metadata: mf2 classes (~15G)
# # https://bigquery.cloud.google.com/savedquery/464705913036:19a763c26f5440bdbcf2eeb12b806641
# bq --format=prettyjson query > site_extra_mf2.$1.json <<EOF
# SELECT domain, ARRAY_AGG(DISTINCT m IGNORE NULLS) AS mf2_classes
# FROM indiemap.canonical_pages p, p.mf2_classes m
# GROUP BY domain;
# EOF


# ~/src/indie-map/src/make_web.py site.$1.json.gz links.$1.json site_extra*.$1.json

# gsutil cp base/$1.json gs://www.indieweb.org/
# gsutil cp indieweb/$1.json gs://www.indieweb.org/indie/
# gsutil cp full/$1.json gs://www.indieweb.org/full/

# ~/src/indie-map/src/web_to_bigquery.py indie

# ~/src/indie-map/src/make_kumu.py indie
