#!/bin/bash
#
# Reads a list of domains from stdin, fetches them over HTTP, follows
# redirections, and emits the final domains (whether the same or different) to
# stdout.
#
# Includes a blacklist of common non-indieweb domains, e.g. silos.

while read domain; do
  redirected=`curl -v -i -L -o /dev/null $domain 2>&1 \
    | grep -E '^< Location: ' \
    | tail -n 1 \
    | sed -E 's/^< Location: https?:\/\/([^/]+)\/?.*/\1/'`
  echo ${redirected:-$domain}
done

# archive.org
# accounts.google.com
# bit.ly
# bitly.com
# buff.ly
# buffer.com
# fb.me
# getpocket.com
# goo.gl
# google.com
# ifttt.com
# j.mp
# ow.ly
# plus.google.com
# pocket.co
# t.co
# twitter.com
# vk.com
# web.archive.org
# wp.me
# wordpress.com
# www.facebook.com
# www.linkedin.com
# www.pinterest.com
# www.reddit.com
# www.tumblr.com
