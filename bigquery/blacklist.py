"""Miscellaneous blacklists."""
import re

# known WordPress URL query params that redirect back to the current page or to
# silos, from e.g. the ShareDaddy plugin.
URL_BLACKLIST_RE = re.compile(r"""
  [?&]
    (shared?=(email|facebook|google-plus-1|linkedin|pinterest|pocket|reddit|skype|telegram|tumblr|twitter|youtube) |
    like_comment= |
    replytocom= |
    redirect_to= ) |
  /index\.php\?title= |
  ^https?://chat\.indieweb\.org/([^/]+/)?....-..-../[0-9]+ |
  ^https?://indieweb\.org/irc/([^/]+/)?....-..-../line/[0-9]+ |
  ^https://waterpigs\.co\.uk/mentions/webmention/\?wmtoken= |
  ^http://www.ogok.de/search\?
  """, re.VERBOSE)
