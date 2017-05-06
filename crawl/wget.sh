#!/bin/bash

wget --recursive --level=inf --no-check-certificate --timeout=120 --no-verbose \
    --adjust-extension --convert-links --wait=.3 --random-wait --tries=5 \
    --follow-tags=a \
    --reject="as,atom,avi,bz2,bzip,bzip2,css,csv,doc,docx,exe,gif,GIF,gz,GZ,gzip,ico,iso,jar,jpeg,JPEG,jpg,JPG,js,json,m4a,m4b,m4v,mov,mp3,mp4,mpg,odt,ogg,pdf,png,PNG,rar,rdf,rss,svg,swf,SWF,tar,txt,text,wav,wma,wmv,xml,xpi,Z,zip,[?&]_t=amp,[?&]_t=rss" \
    --append-output=log2 --warc-file=$1 $1 \
    --reject-regex '.*[?&](shared?=(email|facebook|google-plus-1|linkedin|pinterest|pocket|reddit|skype|telegram|tumblr|twitter|youtube)|like_comment=|replytocom=|redirect_to=).*' \
    || true

    # only for rhiaro.co.uk:
    # --header='Accept: text/html' \
