#!/bin/bash
#
# Crawls new (uncommitted) domains in domains.txt with wget --recursive.
#
# Detects new domains with git diff. Writes crawled files to a directory and a
# gzipped WARC file for each domain.

# xargs stops if any command returns non-zero exit code, but we want to be able
# to kill individual domain crawls, so use 'wget ... || true' to always return 0.

git diff --no-color --word-diff=porcelain README.md \
  | grep -E '^\+[^+]' \
  | xargs -I %% -n 1 -P 10 -t sh -c \
    'wget --recursive --level=inf --no-check-certificate --timeout=120 --no-verbose \
      --adjust-extension --convert-links --wait=.5 --random-wait --tries=3 \
      --follow-tags=a --warc-file=%% %% \
      --reject=avi,bz2,bzip,bzip2,css,csv,doc,docx,exe,gif,GIF,gz,GZ,gzip,ico,iso,jar,jpeg,JPEG,jpg,JPG,js,json,m4a,mov,mp3,mp4,mpg,odt,ogg,pdf,png,PNG,rar,rdf,svg,swf,SWF,tar,txt,text,wav,wmv,xml,xpi,Z,zip \
      || true' \
  >& log
