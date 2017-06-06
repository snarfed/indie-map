-- BigQuery views and queries.
-- https://bigquery.cloud.google.com/dataset/indie-map:indiemap
--
-- I should eventually switch this to just an export of the saved views and
-- queries there, instead of duplicating them here.

-- View: canonical_pages
-- (I originally used a function for SPLIT(url, '://')[SAFE_OFFSET(1)] etc, but
-- BigQuery doesn't allow functions in views.)
WITH extras AS (
    SELECT *, SPLIT(url, '://')[SAFE_OFFSET(1)] AS norm_url,
           (SELECT r.urls FROM UNNEST (rels) r WHERE r.value = 'canonical') AS canonicals
    FROM `indie-map.indiemap.pages`
)
SELECT *
FROM extras
WHERE ARRAY_LENGTH(u_urls) = 0 OR
      norm_url IN (SELECT SPLIT(u_url, '://')[SAFE_OFFSET(1)] FROM UNNEST (u_urls) AS u_url)
   OR ARRAY_LENGTH(canonicals) = 0 OR
      norm_url IN (SELECT SPLIT(c_url, '://')[SAFE_OFFSET(1)] FROM UNNEST (canonicals) AS c_url)

-- View: links_with_domains_mf2
SELECT
  p.url AS from_url,
  p.domain AS from_domain,
  l.url AS to_url,
  NET.HOST(l.url) AS to_domain,
  CASE
    WHEN 'u-in-reply-to' IN UNNEST (l.classes) THEN 'u-in-reply-to'
    WHEN 'u-repost-of' IN UNNEST (l.classes) THEN 'u-repost-of'
    WHEN 'u-like-of' IN UNNEST (l.classes) THEN 'u-like-of'
    WHEN 'u-favorite-of' IN UNNEST (l.classes) THEN 'u-favorite-of'
    WHEN 'u-invitee' IN UNNEST (l.classes) THEN 'u-invitee'
    WHEN 'u-quotation-of' IN UNNEST (l.classes) THEN 'u-quotation-of'
    WHEN 'u-bookmark-of' IN UNNEST (l.classes) THEN 'u-bookmark-of'
    ELSE NULL
  END AS mf2_class
FROM
  `indie-map.indiemap.canonical_pages` p,
  p.links l
WHERE 'nofollow' NOT IN UNNEST (l.classes)

-- Social graph links
SELECT from_domain, to_domain, mf2_class, COUNT(*)
FROM indiemap.links_with_domains_mf2
WHERE to_domain IS NOT NULL AND to_domain != from_domain
GROUP BY from_domain, to_domain, mf2_class
ORDER BY from_domain, to_domain, mf2_class;

-- Per site info for JSON data files
SELECT
  MIN(time) AS crawl_start,
  MAX(time) AS crawl_end,
  COUNT(*) AS num_pages,
  SUM(LENGTH(html)) as total_html_size,
  ARRAY_AGG(DISTINCT mf2_classes) AS mf2_classes,
  ARRAY_AGG(DISTINCT SELECT value FROM p.headers WHERE name = 'Server') AS servers,
  ARRAY_AGG(DISTINCT SELECT value FROM p.rels WHERE name IN
            ('webmention', 'http://webmention.org/')) AS webmention_endpoints,
  ARRAY_AGG(DISTINCT SELECT value FROM p.rels WHERE name IN
            ('micropub', 'http://micropub.net/')) AS micropub_endpoints,
FROM `indie-map.indiemap.pages` p
GROUP BY domain;


-- Find rows with the biggest values in each column. Useful since BigQuery has
-- an undocumented 100MB limit on the amount of data processed per row in a
-- query. (These queries aren't currently saved in BigQuery.)
SELECT p.url, BYTE_LENGTH(html) len
FROM indiemap.pages p
GROUP BY p.url
ORDER BY len DESC

SELECT p.url, BYTE_LENGTH(mf2) len
FROM indiemap.pages p
GROUP BY p.url
ORDER BY len DESC

SELECT p.url, SUM(BYTE_LENGTH(p.u_urls)) len
FROM indiemap.pages p
GROUP BY p.url
ORDER BY len DESC

SELECT url, SUM(BYTE_LENGTH(r.value) + BYTE_LENGTH(ARRAY_TO_STRING(r.urls, ''))) len
FROM indiemap.pages p, p.rels r
GROUP BY p.url
ORDER BY len DESC

SELECT url, SUM(BYTE_LENGTH(h.value) + BYTE_LENGTH(h.name)) len
FROM indiemap.pages p, p.headers h
GROUP BY p.url
ORDER BY len DESC

SELECT p.url, SUM(
  BYTE_LENGTH(l.inner_html) +
  BYTE_LENGTH(l.url) +
  BYTE_LENGTH(ARRAY_TO_STRING(l.classes, '')) +
  BYTE_LENGTH(ARRAY_TO_STRING(l.rels, ''))
  ) len
FROM indiemap.pages p, p.links l
GROUP BY p.url
ORDER BY len DESC

SELECT p.url, SUM(BYTE_LENGTH(m)) len
FROM indiemap.pages p, p.mf2_classes m
GROUP BY p.url
ORDER BY len DESC

-- Alternative: run this (in tcsh) over the per site json.gz files.
-- foreach f (*.json.gz)
--   echo `gzcat $f | wc -L`  $f
-- end
