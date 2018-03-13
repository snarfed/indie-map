Indie Map
===

[Indie Map](http://www.indiemap.org/) is a public [IndieWeb](https://indieweb.org/) social graph and dataset. [See the docs for details.](http://www.indiemap.org/docs.html) This doc focuses on how to develop, run, and maintain Indie Map itself.

The individual sites and pages retain their original copyright. The rest of the dataset and this project are placed into the public domain via the [CC0 public domain dedication](http://creativecommons.org/publicdomain/zero/1.0/).


### Crawl

The crawler is basically just `xargs wget -r < domains.txt`. Details in [`crawl.sh`](https://github.com/snarfed/indie-map/blob/master/crawl/crawl.sh) and [`wget.sh`](https://github.com/snarfed/indie-map/blob/master/crawl/wget.sh).

To add a site to the dataset, run `crawl/add_site_1.sh`, then `crawl/add_site_2.sh`. They're separate because `add_site_2.sh` runs ~300GB of BigQuery queries, which costs ~$1.50, so if you're adding lots of sites, run `add_site_1.sh` once for each site and then `add_site_2.sh` once for all the sites together.


#### Extracting IWS 2017 domains

Run this shell command to fetch [2017.indieweb.org](https://2017.indieweb.org/), extract the attendees' web sites, and compare to [`domains_iws2017.txt`](https://github.com/snarfed/indie-map/blob/master/crawl/domains_iws2017.txt) to see if there are any new ones.

```sh
curl https://2017.indieweb.org/ \
  | grep -A2 'class="profile-info"' \
  | grep -o -E 'http[^"]+' \
  | grep -v www.facebook.com \
  | cut -d/ -f3 | sort | uniq \
  | diff ~/src/indie-map/crawl/domains_iws2017.txt -
```

#### Extracting wiki user domains

Run this shell command to fetch a page of IndieWeb wiki users and extract their web site domains:

```sh
curl 'https://indieweb.org/wiki/index.php?title=Special:ListUsers&limit=500' \
  | grep -o -E '"User:[^" ]+' | cut -d: -f2 | grep .
```

...and then follow next page links, e.g. `&offset=Homefries.org`, `&offset=...`


#### Fixing sites.json files in place

When I hit eg:
```
BigQuery error in load operation: Error processing job
'indie-map:bqjob_r9dcbd6e76f81db0_0000015c29d469ee_1': JSON table encountered too many
errors, giving up. Rows: 57; errors: 1.
Failure details:
- file-00000000: JSON parsing error in row starting at position
3088711: . Only optional fields can be set to NULL. Field: names;
Value: NULL
```

I deleted the offending null values manually with e.g.:

```sh
grep '"names": \[[^]]*null[^]]*\]' sites.json |cut -d, -f1
sed -i '' 's/"names":\ \[null\]/"names":\ []/' sites.json
sed -i '' 's/"names":\ \[null,\ /"names":\ [/' sites.json
sed -i '' 's/"names":\ \["Jeremy Zilar",\ null,/"names":\ ["Jeremy Zilar",/' sites.json
```


#### Finding sites that redirected to other domains (to add those too)

```sh
foreach f (*.warc.gz)
echo --
echo $f
gzcat $f | head -n 100 | grep -m 2 -A20 -E '^HTTP/1\.[01] (30.|403)' | grep -E '^(HTTP/1|Location:)'
end
```

then massage manually, with e.g. these Emacs regexp replaces:

```
.+\.warc\.gz
--

^\(.+\)\.warc\.gz
.+
[Ll]ocation: https://\1/?.*
\(HTTP.*
\)?--

^\(.+\)\.warc\.gz
.+
[Ll]ocation: /.*
\(HTTP.*
\)?--

^.+.warc.gz
HTTP/1.1 403 Forbidden
--


^.+\.warc\.gz
.+
[Ll]ocation: https?://\([^/]+\)/?.*
\(HTTP.*
\)?--
=>
\1
```


### Ops and setup

#### Web site

I did this to set up [www.indiemap.org](http://www.indiemap.org/) to [serve from Google Cloud Storage](https://cloud.google.com/storage/docs/hosting-static-website) and store HTTP request logs in `gs://indie-map/`:

```sh
gsutil mb www.indiemap.org
gsutil cp www/index.html gs://www.indiemap.org/
gsutil cp www/docs.html gs://www.indiemap.org/
gsutil cp www/404.html gs://www.indiemap.org/
gsutil acl ch -u AllUsers:R gs://www.indiemap.org/index.html
gsutil web set -m index.html -e 404.html gs://www.example.com

# https://cloud.google.com/storage/docs/access-logs
gsutil acl ch -g cloud-storage-analytics@google.com:W gs://indie-map
gsutil logging set on -b gs://indie-map -o logs/ gs://www.indiemap.org/

# https://cloud.google.com/storage/docs/access-control/create-manage-lists#defaultobjects
gsutil defacl ch -u AllUsers:READER gs://www.indiemap.org
```

#### Copying files to GCS

I ran these commands to copy the initial WARCs, BigQuery input JSON files, and social graph files to GCS and load them into BigQuery:

```sh
gsutil -m cp -L cp.log *.warc.gz gs://indie-map/crawl/
gsutil -m cp -L cp.log *.json.gz gs://indie-map/bigquery/

# can gsutil -m rsync ... as final sync. can also sanity check with:
ls -1 *.{json,warc}.gz | wc
gsutil ls gs://indie-map/{crawl,bigquery}/ | wc
du -c -b *.{json,warc}.gz | wc
gsutil du -sc gs://indie-map/{crawl,bigquery}/ | wc

# https://cloud.google.com/bigquery/bq-command-line-tool
bq load --replace --autodetect --source_format=NEWLINE_DELIMITED_JSON indiemap.pages gs://indie-map/bigquery/\*.json.gz
bq load --replace --autodetect --source_format=NEWLINE_DELIMITED_JSON indiemap.sites sites.json.gz
# then watch job at https://bigquery.cloud.google.com/jobs/indie-map
```


#### Python snippets for debugging WARC files

```py
import gzip
from bs4 import BeautifulSoup, UnicodeDammit
import mf2py
import warcio

with gzip.open('FILE.warc.gz', 'rb') as input:
  for i, record in enumerate(warcio.ArchiveIterator(input)):
    if i == 178:
      body = UnicodeDammit(record.content_stream().read()).unicode_markup
      break

record.rec_type
record.rec_headers.get('WARC-Target-URI')
print(body)
```
