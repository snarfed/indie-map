"""URLs that are infinite loops, randomly generated, or otherwise low value."""
import re

URL_BLACKLIST_RE = re.compile(r"""
  [?&]
    (shared?=(email|facebook|google-plus-1|linkedin|pinterest|pocket|reddit|skype|telegram|tumblr|twitter|youtube) |
    like_comment= |
    replytocom= |
    redirect_to= ) |
  /index\.php\?title= |
  ^https?://adactio.com/extras/talklikeapirate/translate.php\? |
  ^https?://chat\.indieweb\.org/([^/]+/)?....-..-../[0-9]+ |
  ^https?://indieweb\.org/irc/([^/]+/)?....-..-../line/[0-9]+ |
  ^https://waterpigs\.co\.uk/mentions/webmention/\?wmtoken= |
  ^http://www\.ogok\.de/search\? |
  ^https://shkspr\.mobi/plays\.php\?.*&start=- |
  ^http://nullroute\.eu\.org/mirrors/shoujoai\.com/ |
  ^http://vasilis\.nl/random/daily/.*\.svg |
  ^https://webdesign\.weisshart\.de/suchen\.php\? |
  ^http://tilde\.club/~odwyer/maze/[0-9a-f]{32} |
  ^http://fastwonderblog\.com/.*/(consulting/|speaking/){3,} |
  ^http://jothut\.com/cgi-bin/junco\.pl/.*/%5C%22http://toledo |
  ^http://pflanzen-bild\.de/.*/\?s= |
  ^http://www\.bakera\.de/dokuwiki/doku.php/.*\? |
  ^http://www\.xmlab\.org/news/blog-post/.*/news/blog-post/ |
  ^http://amitp.blogspot.com/.*?widgetType=BlogArchive
  """, re.VERBOSE)
