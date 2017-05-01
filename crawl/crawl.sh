#!/bin/bash
#
# Crawls new (uncommitted) domains in domains.txt with wget --recursive.
#
# Detects new domains with git diff. Writes crawled files to a directory and a
# gzipped WARC file for each domain.

# xargs stops if any command returns non-zero exit code, but we want to be able
# to kill individual domain crawls, so use 'wget ... || true' to always return 0.

cd `dirname $0`
DOMAINS=`git diff --no-color --word-diff=porcelain domains.txt \
           | grep -E '^\+[^+]' | cut -c2-`
echo $DOMAINS
cd -

echo $DOMAINS | xargs -I %% -n 1 -P 30 -t `dirname $0`/wget.sh %%
