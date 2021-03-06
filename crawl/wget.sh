#!/bin/bash

wget --recursive --level=inf --no-check-certificate --timeout=60 --no-verbose \
    --adjust-extension --continue --wait=.1 --random-wait --waitretry=1 --tries=5 \
    --follow-tags=a \
    --reject="as,atom,avi,bz2,bzip,bzip2,css,csv,doc,docx,dvf,eot,epub,exe,gif,GIF,gz,GZ,gzip,ico,iso,jar,jpeg,JPEG,jpg,JPG,js,json,m4a,m4b,m4v,mov,mp3,mp4,mpg,odt,ogg,pdf,PDF,png,PNG,ppt,pptx,ps,rar,rdf,rss,svg,swf,SWF,tar,text,ttf,txt,wav,wma,wmv,woff2,xml,xls,xlsx,xpi,Z,zip,[?&]_t=amp,[?&]_t=rss" \
    --append-output=log --warc-file=$1 $1 \
    --reject-regex '.*([?&](shared?=(email|facebook|google-plus-1|linkedin|pinterest|pocket|press-this|reddit|skype|telegram|tumblr|twitter|youtube)|like_comment=|replytocom=|redirect_to=)|/index\.php\?title=|(chat\.)?indieweb\.org/([^/]+/)?....-..-../[0-9]+).*|/search\?|/sudokant.cgi\?|//huffduffer\.com/(.+/)*(login/|tags/|related)|/translate\.php|/suchen\.php|//(bzr|dokuwiki|git|mirrors)/|//dev\.subversive\.audio/agenda/|//dracos\.co\.uk/made/bbc-news-archive/|//fastwonderblog\.com/category/|//halfanhour\.blogspot\.com/search|//jothut\.com/cgi-bin/junco/.pl|//thecommandline\.net/wiki/|//tilde\.club/~odwyer/maze/|//vasilis\.nl/random/daily/|//waterpigs\.co\.uk/mentions/webmention/|//www\.ogok\.de/search|//www\.rmendes\.net/tag/|//www\.xmlab\.org/news/blog-post/|//wirres\.net/imagecatalogue/' \
    --user-agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:53.0) Gecko/20100101 Firefox/53.0' \
    || true

    # only for rhiaro.co.uk:
    # --header='Accept: text/html' \
