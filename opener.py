# -*- encoding:utf-8 -*-
'''UAを設定したurlopener '''
import urllib2
opener = urllib2.build_opener()
opener2 = urllib2.build_opener()
opener.addheaders = [\
('Use-Agent', 'Mozilla/5.0 (compatible; googlebot/2.1; \
+ http://www.google.com/bot.html)')]
opener2.addheaders = [\
('User-Agent', 'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; ja-jp) \
AppleWebKit/417.9(KHTML, like Gecko) Safari/125.9')]
