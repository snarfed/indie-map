Indie Map
===
A collection of [Indie Web](http://indieweb.org/) sites.

This project is placed into the public domain. You may also use it under the [CC0 license](http://creativecommons.org/publicdomain/zero/1.0/).

Manual crawl
====
See crawl/crawl.sh.

Inclusion criteria: microformats2, webmention endpoint, or micropub endpoint. Subject to judgment calls, e.g. achor.net has mf2 but is a *massive* forum (>20G of HTML!) and isn't really part of the community.

notable:
indieweb.org: obvs. also mediawiki sites are big with revision history, etc.
brid.gy: large collection of h-cards! :P
tantek.com, aaronparecki.com, kevinmarks.com, caseorganic.com: IWC founders!
cyborganthropology.com: mediawiki.
loadaverage.org: somewhat big gnu social instance.


Common Crawl
====
I originally tried extracting sites with microformats2 or a webmention or micropub endpoint from the [Common Crawl](http://commoncrawl.org/), but it turned out to be too big. The latest crawl (~2B pages) wasn't enough; they deliberately spread out the URL space, so I would have needed to process *all* of their crawls, and even then I wouldn't be guaranteed to see all pages on a given site.

I considered ignoring domains in a blacklist that I know aren't Indie Web, e.g. facebook.com and twitter.com. [Bridgy's blacklist](https://github.com/snarfed/bridgy/blob/master/domain_blacklist.txt) and the Common Crawl's top 500 domains (`s3://commoncrawl/crawl-analysis/CC-MAIN-2017-13/stats/part-00000.gz`) were good sources. However, in the March 2017 crawl, those top 500 domains comprise just ~505M of the >3B total pages (ie 1/6), which isn't substantial enough to justify the risk of missing anything.

Some parts of [cc-mrjob](https://github.com/commoncrawl/cc-mrjob/) are included in the `commoncrawl/` subdirectory under the [MIT License](https://github.com/commoncrawl/cc-mrjob/blob/master/LICENSE).
