Indie Map
===
Indie Map is a public IndieWeb [IndieWeb](https://indieweb.org/) social graph and dataset. See [indiemap.org](http://www.indiemap.org/) for details.

The individual sites and pages retain their original copyright. The rest of the dataset and this project are placed into the public domain. You may also use it under the [CC0 license](http://creativecommons.org/publicdomain/zero/1.0/).


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
Crawler is basically just `xargs wget < domains.txt`. Details in [`crawl.sh`](https://github.com/snarfed/indie-map/blob/master/crawl/crawl.sh) and [`wget.sh`](https://github.com/snarfed/indie-map/blob/master/crawl/wget.sh).
