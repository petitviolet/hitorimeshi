# -*- encoding:utf-8 -*-

from urllib2 import urlopen
import MySQLdb
from lxml import etree
from time import sleep
import glob
import os

# いろいろ
from secret import db, host, user, passwd, charset, \
        TAGNAMES, TABELOG_URL, CACHE_DIR, CACHE_FILE, API_KEY
from stations import STATIONS

def main():
    '''既にリクエストしてキャッシュしてあるものは除外して
    tabelogにリクエストをする
    '''
    requested_count = 0  # apiは1日200回
    already_indexed = {}
    # cacheディレクトリからすでにダウンロード済みのものを取得する

    # とりあえず大阪を取る
    # 次は東京
    for i in xrange(13, 14):
    # for i in xrange(1, 48):
        try:
            already_indexed['{i:>02d}'.format(i=i)] = \
                    ' '.join(glob.glob('./cache/{i:>02d}/*.xml'.format(i=i)))
        except:
            continue

    # まだindexされていないものをindexする
    for f_index, stations in STATIONS.iteritems():
        # とりあえず大阪を取る
        # 次は東京
        if f_index != '13':
            continue
        for station in stations:
            requested_count += 1
            if requested_count == 200:
                return '一旦終了'
            if station in already_indexed[f_index]:
                continue
            print station + '----------'
            try:
                values = request_tabelog(f_index, station)
            except ValueError as e:
                print e
                return
            save_tabelog_values(values)

TO_BE_EXIT = False  # 2回連続で400エラーなら終了する

def request_tabelog(f_index, station=None):
    '''tabelogのapiにリクエストを送る
    【京都版】なので京都府限定で、駅名を引数に渡すと、その近辺で検索する
    結果をキャッシュとしてDBに保存する
    '''
    values = []
    global TO_BE_EXIT
    # apiの仕様で60ページしかとれない
    for i in xrange(1, 61):
        print '  %d番目' % i
        sleep(3)
        url = TABELOG_URL.format(page_num=i, api_key=API_KEY, station=station)
        cache_dir = CACHE_DIR.format(f_index = f_index)
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        try:
            # httpアクセスと、その応答をファイルキャッシュ
            html = urlopen(url).read()
            cache_fname = cache_dir + station + '_' + str(i) + CACHE_FILE
            save_cache_html(cache_fname, html)
            TO_BE_EXIT = False
        except Exception as e:
            print 'エラー！=> ', e
            if TO_BE_EXIT:
                raise ValueError('終わり!')
            TO_BE_EXIT = True
            break
        values.extend(extract_item_from_html(html))
    return values

def values_from_cachefile(f_index):
    '''ファイルキャッシュからデータを読み込む
    '''
    values = []
    xml_files = glob.glob('./cache/{f_index:<02}/*.xml'.format(f_index=f_index))
    for xml_file in xml_files:
        html = open(xml_file, 'r').read().strip()
        values.extend(extract_item_from_html(html))
    return values

def save_tabelog_values(values):
    '''リクエストに対する結果をDBに保存する
    '''
    con = MySQLdb.connect(db=db, host=host,\
            user=user, passwd=passwd, charset=charset)
    cur = con.cursor()
    # geometry型に変換する
    sql = "replace into tabelog (" + ", ".join(TAGNAMES) \
            + ") values (" + "%s, " * 17 + "GeomFromText('POINT(%s %s)'));"
    cur.executemany(sql, values)
            # + ') values (' + '%s,' * 18 + '%s)', values)
    return cur, con
    # con.commit()
    # cur.close()
    # con.close()

def extract_item_from_html(html):
    '''htmlをlxmlでパースして各Itemをリスト化する
    崩れたxmlをなんとかする
    '''
    result = []
    xml_root = etree.fromstring(html, etree.XMLParser(recover=True))
    items = xml_root.xpath('//Item')
    for item in items:
        result.append(parse_tag(item))
    return result


def save_cache_html(fname, html):
    '''xmlファイルをそのままファイルとして保存
    '''
    if not os.path.exists(fname):
        with open(fname, 'w') as f:
            f.write(html)

def parse_tag(item):
    '''リクエスト結果のItemをDBに格納できる形に変換
    '''
    # item_dict = {}
    value = []
    for tag in item:
        value.append(MySQLdb.escape_string(tag.text.replace(',', ' ').encode('utf-8')) if tag.text else tag.text)
    # latitudeとlongitudeを入れ替える
    value[-2], value[-1] = float(value[-1]), float(value[-2])
    return tuple(value)
# if i == 0:
        #     item_dict['Rcd'] = tag.text
        # elif i == 1:
        #     item_dict['RestaurantName'] = tag.text
        # elif i == 2:
        #     item_dict['TabelogUrl'] = tag.text
        # elif i == 3:
        #     item_dict['TabelogMobileUrl'] = tag.text
        # elif i == 4:
        #     item_dict['TotalScore'] = tag.text
        # elif i == 5:
        #     item_dict['TasteScore'] = tag.text
        # elif i == 6:
        #     item_dict['ServiceScore'] = tag.text
        # elif i == 7:
        #     item_dict['MoodScore'] = tag.text
        # elif i == 8:
        #     item_dict['Situation'] = tag.text
        # elif i == 9:
        #     item_dict['DinnerPrice'] = tag.text
        # elif i == 10:
        #     item_dict['LunchPrice'] = tag.text
        # elif i == 11:
        #     item_dict['Category'] = tag.text
        # elif i == 12:
        #     item_dict['Station'] = tag.text
        # elif i == 13:
        #     item_dict['Address'] = tag.text
        # elif i == 14:
        #     item_dict['Tel'] = tag.text
        # elif i == 15:
        #     item_dict['BusinessHours'] = tag.text
        # elif i == 16:
        #     item_dict['Holiday'] = tag.text
        # elif i == 17:
        #     item_dict['Latitude'] = tag.text
        # elif i == 18:
        #     item_dict['Longitude'] = tag.text
    # return item_dict

if __name__ == '__main__':
    main()
