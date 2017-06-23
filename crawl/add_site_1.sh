#!/bin/bash
#
# Run to do the first half of adding a new site. Second half is add_site_2.sh.
#
# Usage: add_site_1.sh DOMAIN

set -x
set -e

~/src/indie-map/crawl/wget.sh $1

gsutil cp $1.warc.gz gs://indie-map/crawl/

source ~/src/indie-map/src/local/bin/activate
~/src/indie-map/src/warc_to_bigquery.py $1.warc.gz

gsutil cp $1.json.gz gs://indie-map/bigquery/
bq load --source_format=NEWLINE_DELIMITED_JSON indiemap.pages gs://indie-map/bigquery/$1.json.gz

echo $1 | ~/src/indie-map/src/sites_to_bigquery.py >> sites.json


