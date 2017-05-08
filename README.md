Indie Map
===
A queryable dataset of [IndieWeb](https://indieweb.org/) sites, pages, and inferred social graph.

The individual sites and pages retain their original copyright. The rest of the dataset and this project are placed into the public domain. You may also use them under the [CC0 license](http://creativecommons.org/publicdomain/zero/1.0/).


Schema
---
`Page`
* `url`
* `domain`
* `time`: fetch timestamp
* `headers`: HTTP response headers, array of (name, value)
* `HTML`: raw page content
* `links`: outbound links extracted from `href`s of `a` and `link` tags. array of (URL, inner HTML, HTML tag (`a` or `link`), array of rel values, array of classes)
* `mf2`: full JSON mf2 parsed from page, encoded as string. Can query in BiqQuery with [`JSON_EXTRACT`](https://cloud.google.com/bigquery/docs/reference/legacy-sql#json_extract) plus [JSONPath](https://code.google.com/p/jsonpath).
* `mf2_classes`: array of unique mf2 classes found in page
* `rels`: array of `rel` values from parsed mf2
* `u_urls`: array of unique top-level mf2 `u-url`s


`Site`
* domain
* homepage meta
  * `<title>`
  * Open Graph data: `<meta property="og:...">...`
  * rel links: micropub, webmention, authorization_endpoint
  * rel-me links
* authorship: [`h-card`](http://microformats.org/wiki/h-card#Properties)
  * `p-name`
  * `u-photo` or `u-logo`
  * `u-url`
  * `p-label`
* social graph
  * other domains ranked by outbound links, by domain scored by type. maybe reply more then like, outbound more than inbound comment, etc.
  * special case silos to include username in links

Also serve the `Site` table as a JSON file per site, e.g. `https://indie-map.org/site/snarfed.org.json`.

Also serve the raw WARCs?

If I was to use a Graph DB instead of BigQuery:
* [Appbase](https://appbase.io/)
* [Real-Time Graph Database As a Service with Appbase](https://scotch.io/tutorials/real-time-graph-database-as-a-service-with-appbase)
* [GrapheneDB](https://www.graphenedb.com)


Statistics
---
* Total http requests, bytes
* HTML pages fetched (ie HTTP 200), bytes
* Links: total, internal
* mf2 classes, instances
* Pages with mf2, webmention endpoint, micropub endpoint, auth endpoint
  * Distinct endpoints
* Domains: served, redirected, failed
  * ... with mf2, webmention, micropub, auth endpoints


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


Manual crawl
---
See crawl/crawl.sh.

Inclusion criteria: microformats2, webmention endpoint, or micropub endpoint. Subject to judgment calls, e.g. achor.net has mf2 but is a *massive* forum (>20G of HTML!) and isn't really part of the community.

Notable sites:
indieweb.org, chat.indieweb.org
brid.gy: large collection of h-cards! :P
tantek.com, aaronparecki.com, kevinmarks.com, caseorganic.com: IWC founders!
loadaverage.org: somewhat big gnu social instance.


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
