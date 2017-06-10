#!/bin/bash
#
# Reads a list of domains from stdin, fetches them over HTTP, follows
# redirections, and emits the final domains (whether the same or different) to
# stdout.

while read domain; do
  redirected=`curl -v -i -L -o /dev/null $domain 2>&1 \
    | grep -E '^< Location: ' \
    | tail -n 1 \
    | sed -E 's/^< Location: https?:\/\/([^/]+)\/?.*/\1/'`
  echo ${redirected:-$domain}
done
