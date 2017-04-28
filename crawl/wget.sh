#!/bin/bash

wget --recursive --level=inf --no-check-certificate --timeout=120 --no-verbose \
    --adjust-extension --convert-links --wait=.3 --random-wait --tries=5 \
    --follow-tags=a \
    --reject="as,atom,avi,bz2,bzip,bzip2,css,csv,doc,docx,exe,gif,GIF,gz,GZ,gzip,ico,iso,jar,jpeg,JPEG,jpg,JPG,js,json,m4a,m4b,m4v,mov,mp3,mp4,mpg,odt,ogg,pdf,png,PNG,rar,rdf,rss,svg,swf,SWF,tar,txt,text,wav,wma,wmv,xml,xpi,Z,zip,[?&]_t=amp,[?&]_t=rss" \
    --header='Accept: text/html' \
    --warc-file=$1 $1 \
    || true


#    --exclude-domains accounts.google.com,getpocket.com,google.com,twitter.com,www.facebook.com,www.linkedin.com,www.pinterest.com,www.reddit.com,www.tumblr.com \
