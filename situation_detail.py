#!/usr/local/bin/python
# -*- encoding:utf-8 -*-
from opener import opener
from math import log, sqrt
from collections import defaultdict
from BeautifulSoup import BeautifulSoup as bs
import MySQLdb
import cPickle
from time import sleep
from secret import db, host, user, passwd, charset
import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '/app')
from Table import Session, UserPost
from datetime import datetime

def save_tabelog_situations():
    '''tabelogのhtmlから使用用途をスクレイピング
    「一人で」の割合を取得する
    DBからurlを取得し、まだindexしていないurlについてスクレイピング
    '''
    con = MySQLdb.connect(db=db, host=host,\
                user=user, passwd=passwd, charset=charset)
    cur = con.cursor()
    # geometry型に変換する
    # cur.executemany(sql, values)
            # + ') values (' + '%s,' * 18 + '%s)', values)
    sql = ('select TabelogURL from tabelog where Rcd not in'
            '(select rst_id from user_post)')
    # sql = 'select TabelogURL from tabelog'
    fname = 'situation.dict'
    dic = load_pickle(fname)
    if dic:
        print '{fname}を読み込み'.format(fname=fname)
    else:
        dic = defaultdict(dict)
        print 'ファイルを新規作成'
    count = cur.execute(sql)
    # 既にindexしているurlは除く
    _urls = [url[0] for url in cur.fetchall()]
    urls = [url for url in _urls if url not in dic.keys()]
    count = len(urls)
    for i, url in enumerate(urls):
        print '{count} url中: {num} url目'.format(count=count, num=i+1)
        original_url = url
        rating_url = url + 'dtlratings/'
        # urlにアクセスして使用用途の割合を取得する
        try:
            total, lonly = lonly_rate_of_url(rating_url)
        except Exception, e:
            print e
            total, lonly = 0.0, 0.0
        try:
            rate = lonly / total
        except ZeroDivisionError, e:
            rate = None
        print '{url} => {rate}:({lonly} / {total})'\
                .format(url=original_url, rate=rate, \
                        lonly=lonly, total=total)
        # dicはkeyがurlで、総数・一人・(一人/総数)がvalue
        dic[original_url]['total'] = total
        dic[original_url]['lonly'] = lonly
        dic[original_url]['rate'] = rate
        print '==============================sleeping...'
        sleep(5)
    # とりあえずピクル化しておく
    with open('situation.dict', 'w') as f:
        cPickle.dump(dic, f)
    cur.close()
    con.close()
    return True

def set_default_difficulty(fname='situation.dict'):
    print 'load_pickle ... ',
    dic = load_pickle(fname)
    print 'done.'
    scores = calc_default_difficulty(dic)
    print 'calc_default_difficulty ... done.'
    del dic
    con = MySQLdb.connect(db=db, host=host,\
            user=user, passwd=passwd, charset=charset)
    cur = con.cursor()
    user_id, comment = 19, ''
    get_rstid = 'select Rcd from tabelog where tabelogurl = %s limit 1'
    session = Session()
    i, count = 1, len(scores)
    for_add = []
    for url, difficulty in scores.iteritems():
        print '{i} / {count} url'.format(i=i, count=count)
        difficulty = round(difficulty, 1)
        i += 1
        result = cur.execute(get_rstid, url)
        rst_id = cur.fetchone()[0] if result else None
        now = datetime.now()

        userpost = session.query(UserPost)\
                .filter('user_id = :user_id and rst_id = :rst_id')\
                .params(user_id=user_id, rst_id=rst_id).first()
        if userpost:
            print 'update'
            userpost.modified = now
            userpost.difficulty = difficulty
            userpost.comment = comment
        else:
            print 'insert'
            user_post = UserPost(user_id, rst_id, difficulty, comment, now, now)
            # session.begin()
            for_add.append(user_post)
    try:
        session.add_all(for_add)
        session.flush()
        session.commit()
        session.close()
    except Exception ,e:
        session.rollback()
        print e
        session.close()
        return False
    return True


def load_pickle(fname):
    '''cPickleをロードする
    '''
    try:
        with open(fname, 'r') as f:
            pickled_file = cPickle.load(f)
        return pickled_file
    except Exception as e:
        print e
        return False

def calc_default_difficulty(situations=load_pickle('situation.dict')):
    '''初期値となる難易度を計算する
    計算式は直感
    '''
    # スコアを(lonly, total)から計算する。適当。
    s = lambda x: sqrt(sqrt(x))
    calc = lambda t, l: log(s(t - l + 1) * ((t + 0.1) / (l + 0.1)) * s(t + 1))
    result, scores = {}, {}
    for k, v in situations.iteritems():
        # 評価が存在しない店についてはNoneにしておく
        scores[k] = calc(v['total'], v['lonly']) if v['rate'] else None
    # 最大値と最小値のうち、中央値との差が大きい方をとり、
    # その値が5.0または1.0となるようにするためのbiasを求める
    values = [v for v in scores.values() if v]  # None以外の値についてのみ
    max_value = max(values)
    mid_value = values[len(values) / 2]
    min_value = min(values)
    del values  # もういらない
    # 最大値と中央値の差、 中央値と最小値の差
    top_diff, bottom_diff = max_value - mid_value, mid_value - min_value
    # 値が大きい方を取る
    diff = top_diff if top_diff > bottom_diff else bottom_diff
    bias = 2.0 / diff
    # print max_value, mid_value, min_value, bias
    # 最大値が5になるように正規化
    # 中央値との差にbiasをかけあわせた値を3.0からの差とする
    # Noneの場合は3.0としておく
    normalize = lambda x: 3.0 + bias * (x - mid_value) if x else 3.0
    for k, v in scores.iteritems():
        result[k] = normalize(v)
    return result

# def convert_result(result=calc_default_difficulty()):
#     '''executemanyするために値を変換する
#     (TabelogURL, difficulty)となっているのを入れ替えるだけ
#     '''
#     values = []
#     for k, v in result.iteritems():
#         values.append((v, k))
#     return values

def download_html_into_soup(url):
    '''urlにhttpアクセスしてそれをBeautifulSoup化
    失敗したらFalse
    '''
    try:
        return bs(opener.open(url).read())
    except Exception, e:
        print url, ':', e
        return False

def soup_into_situation_dict(soup):
    '''httpアクセスしてsoup化したものから使用用途を取得し、
    その種類をキーとし、投稿数を値とするdictを作成
    '''
    if not soup:
        return False
    situation_div = soup.find('div', attrs={'class': 'chart-bar-w chart-box'})
    dic = {}
    for situation in situation_div('li'):
        dic[situation.p.text] \
                = int(situation.find('p', {'class': 'num'}).text[1])
    return dic

def calc_lonly_rate(situation_dic):
    '''「一人で」の割合を計算する
    '''
    if not situation_dic:
        return False
    total = sum(situation_dic.values())
    lonly = situation_dic[u'一人で']
    return map(float, [total, lonly])
    # return float(lonly) / total

def lonly_rate_of_url(url):
    '''urlへのhttpアクセス、使用用途の辞書化、「一人で」の割合計算をまとめて実行
    '''
    soup = download_html_into_soup(url)
    situation_dic = soup_into_situation_dict(soup)
    total, lonly = calc_lonly_rate(situation_dic)
    return total, lonly

if __name__ == '__main__':
    save_tabelog_situations()
    set_default_difficulty()
