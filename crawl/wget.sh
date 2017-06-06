#!/bin/bash

wget --recursive --level=inf --no-check-certificate --timeout=120 --no-verbose \
    --adjust-extension --convert-links --wait=.3 --random-wait --tries=5 \
    --follow-tags=a \
    --reject="as,atom,avi,bz2,bzip,bzip2,css,csv,doc,docx,dvf,epub,exe,gif,GIF,gz,GZ,gzip,ico,iso,jar,jpeg,JPEG,jpg,JPG,js,json,m4a,m4b,m4v,mov,mp3,mp4,mpg,odt,ogg,pdf,PDF,png,PNG,ppt,pptx,ps,rar,rdf,rss,svg,swf,SWF,tar,txt,text,wav,wma,wmv,xml,xls,xlsx,xpi,Z,zip,[?&]_t=amp,[?&]_t=rss" \
    --append-output=log --warc-file=$1 $1 \
    --reject-regex '.*([?&](shared?=(email|facebook|google-plus-1|linkedin|pinterest|pocket|reddit|skype|telegram|tumblr|twitter|youtube)|like_comment=|replytocom=|redirect_to=)|/index\.php\?title=|(chat\.)?indieweb\.org/([^/]+/)?....-..-../[0-9]+).*|//huffduffer\.com/(.+/)*(login/|tags/|related)' \
    --user-agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:53.0) Gecko/20100101 Firefox/53.0' \
    || true

    # only for rhiaro.co.uk:
    # --header='Accept: text/html' \
