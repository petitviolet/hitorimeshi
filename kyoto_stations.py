# -*- encoding:utf-8 -*-
'''エキサイトの駅名一覧から駅名を取得する
一回でおわり
'''

from urllib2 import urlopen
import re

# 京都のJR駅名(73駅)
fname = '/var/www/petitviolet.net/public_html/hitorimeshi/kyoto_stations.txt'
STATIONS = open(fname, 'r').read().strip().split(' ')

def main():
    stations = []
    base_url = 'http://www.excite.co.jp/transfer/station/26/?key=%s'
    pages = ['あ','い','う','え','お','か','き','ぎ','く','ぐ','け','こ','ご','さ','し','じ','す','そ','た','だ','ち','つ','て','で','と','ど','な','に','の','は','ひ','ふ','ほ','ま','み','む','も','や','よ','ら','り','ろ','わ']
    p = re.compile('<span class="stationName"><a href=/transfer/station/\d+.html>(.*?)</a></span>')
    for page in pages:
        url = base_url % page
        print page
        try:
            html = urlopen(url).read()
        except:
            print '  continue...'
            continue
        result = p.findall(html)
        stations.extend(result)
    with open('kyoto_stations.txt', 'w+') as f:
        for s in stations:
            f.write(s + ' ')


if __name__ == '__main__':
    main()

