Indie Map
===
Indie Map is a social graph for the [IndieWeb](https://indieweb.org/), and the data to back it up.

The individual sites and pages retain their original copyright. The rest of the dataset and this project are placed into the public domain. You may also use them under the [CC0 license](http://creativecommons.org/publicdomain/zero/1.0/).


Statistics
---
* Total http requests, bytes (currently 77G of gzipped WARCs)
* Complete crawl duration (start, end times)
* HTML pages fetched (ie HTTP 200), bytes
  bigquery: pages 4,056,693
* Links: total, internal
  bigquery: links 481,054,340, link classes 198,121,176
* mf2 classes, instances
* Pages with mf2, webmention endpoint, micropub endpoint, auth endpoint
  * Distinct endpoints
* Conversion time (WARC => BigQuery): ~60h, 5/25-5/27

from WARCs:
* total WARC file size (compressed, uncompressed)
* records
* requests
* responses
* URLs (request and response):
  * host
  * pay level domain
  * TLD
  * SSL or no
* HTTP status code
* HTTP version

from BigQuery pages:
* # pages
* response size
* min, max timestamp
* URLs (request and response):
  * host
  * pay level domain
  * TLD
  * https vs http
* response headers:
  * Content-Type, including encoding
  * Server
  * Content-Length
  * X-Powered-By
  * Last-Modified


UI
---
Requirements:
* GUI for creating queries, dashboards.
* BigQuery support.
* Cheap or free.

Candidates:
* [Metabase](http://www.metabase.com/) [on Heroku](http://www.metabase.com/start/heroku)
* [CoolaData](http://www.cooladata.com/)
* [Qlik](http://www.qlik.com)
* [Kumu](https://kumu.io): mapping UI

If I was to use a Graph DB instead of BigQuery:
* [Appbase](https://appbase.io/)
* [Real-Time Graph Database As a Service with Appbase](https://scotch.io/tutorials/real-time-graph-database-as-a-service-with-appbase)
* [GrapheneDB](https://www.graphenedb.com)


Manual crawl
---
Rough inclusion criteria: microformats2, webmention endpoint, or micropub endpoint. Subject to judgment, e.g. [achor.net](http://achor.net/) has mf2 but is a *massive* forum (>20G of HTML!) and doesn't really participate in the community otherwise.

Crawler is basically just `xargs wget < domains.txt`. Details in [`crawl.sh`](https://github.com/snarfed/indie-map/blob/master/crawl/crawl.sh) and [`wget.sh`](https://github.com/snarfed/indie-map/blob/master/crawl/wget.sh).


Common Crawl
---
I originally tried extracting sites with microformats2 or a webmention or micropub endpoint from the [Common Crawl](http://commoncrawl.org/), but it turned out to be too big. The latest crawl (~2B pages) wasn't enough; they [deliberately spread out the URL space](https://github.com/commoncrawl/cc-crawl-statistics/blob/master/plots/crawloverlap.md), so I would have needed to process *all* of their crawls, and even then I wouldn't be guaranteed to see all pages on a given site.

I considered ignoring domains in a blacklist that I know aren't Indie Web, e.g. facebook.com and twitter.com. [Bridgy's blacklist](https://github.com/snarfed/bridgy/blob/master/domain_blacklist.txt) and the Common Crawl's top 500 domains (`s3://commoncrawl/crawl-analysis/CC-MAIN-2017-13/stats/part-00000.gz`) were good sources. However, in the March 2017 crawl, those top 500 domains comprise just ~505M of the >3B total pages (ie 1/6), which isn't substantial enough to justify the risk of missing anything.

Some parts of [cc-mrjob](https://github.com/commoncrawl/cc-mrjob/) are included in the `commoncrawl/` subdirectory under the [MIT License](https://github.com/commoncrawl/cc-mrjob/blob/master/LICENSE).

Related:
* [Web Data Commons](http://webdatacommons.org/structureddata/#toc1): microformats etc
* [Searching for Microformats, RDFa, and Microdata Usage in the Wild](http://manu.sporny.org/2012/structured-data-searching/)
* [Social Graph Analysis using Elastic MapReduce and PyPy](http://postneo.com/2011/05/04/social-graph-analysis-using-elastic-mapreduce-and-pypy)
* [webarchive-commons](https://github.com/iipc/webarchive-commons)
