# -*- encoding:utf-8 -*-

from Table import Session, Tabelog, User, UserPost, Title, UserStats
import geoalchemy.functions as gf
from sqlalchemy import func
from urllib import urlopen
import json
from datetime import datetime
from judge_title import JudgeTitle

def geo_coding(landmark):
    url = 'http://maps.googleapis.com/maps/api/geocode/json?address={landmark}&sensor=true'
    geo_json = json.load(urlopen(url.format(landmark=landmark)))
    latlng = geo_json['results'][0]['geometry']['location']
    result = {'lat':latlng['lat'], 'lng':latlng['lng']}
    return result


def insert_data(session, new_obj):
    '''new_objを保存し、そのidを返す
    '''
    try:
        # session.begin()
        session.add(new_obj)
        session.flush()
        session.commit()
    except Exception ,e:
        session.rollback()
        print e
        session.commit()
        session.close()
        return False
    inserted_id = new_obj.id
    session.close()
    return inserted_id


##############################
# Tabelog#{{{
##############################

def get_situation(situation):
    '''situationが引数のsituationを含むレストランを取得
    '''
    session = Session()
    try:
        situation = situation.encode('utf-8')
    except:
        pass
    s = session.query(
            Tabelog.id, Tabelog.Rcd, Tabelog.RestaurantName,
            Tabelog.TabelogMobileUrl, Tabelog.TotalScore, Tabelog.Situation,
            Tabelog.DinnerPrice, Tabelog.LunchPrice, Tabelog.Category,
            Tabelog.Station, Tabelog.Address, Tabelog.Tel,
            Tabelog.BusinessHours, Tabelog.Holiday,
            gf.wkt(Tabelog.LatLng).label('Point'))\
            .filter(Tabelog.Situation.like("%{situation}%".format(situation=situation)))
    session.commit()
    session.close()
    return s


def execute_sql_to_tabelog(where):
    '''Tabelogテーブルからwhereに一致するデータを取得
    LatLngをPointにして出力
    '''
    # s = session.query(*(['id']+TAGNAMES[:-1]+['Point'])).from_statement('select '\
    #         + ', '.join(['id'] + TAGNAMES[:-1] + ['AsText(LatLng) as Point']) \
    #         + ' from Tabelog where {where}'.format(where=where)).all()
    # columns = ['Tabelog.id'] + ['Tabelog.'+tag for tag in TAGNAMES[:-1]]
    # s = session.query(*(columns+[gf.wkt('Tabelog.' + TAGNAMES[-1])])).filter(where).all()
    # s = session.query(Tabelog.RestaurantName).filter(where).all()
    session = Session()

    s = session.query(
            Tabelog.id, Tabelog.Rcd, Tabelog.RestaurantName,
            Tabelog.TabelogMobileUrl, Tabelog.TotalScore, Tabelog.Situation,
            Tabelog.DinnerPrice, Tabelog.LunchPrice, Tabelog.Category,
            Tabelog.Station, Tabelog.Address, Tabelog.Tel,
            Tabelog.BusinessHours, Tabelog.Holiday,
            gf.wkt(Tabelog.LatLng).label('Point')).filter(where)
    session.commit()
    session.close()
    return s

def execute_sql(table='tabelog', where=''):
    '''args:
        table => user or user_post
        where => where clause of sql
       returns object of sqlalchemy(all(), order_by, ...)
    '''
    session = Session()
    try:
        if table in ('tabelog', 'Tabelog'):
            raise ValueError('use _execute_sql_to_tabelog instead.')
        elif table in ('user', 'User'):
            s = session.query(User).filter(where)
        elif table in ('user_post', 'UserPost'):
            s = session.query(UserPost).filter(where)
    except Exception:
        # print e
        s = False
    session.commit()
    session.close()
    return s

def _get_margin(zoom=1.0):
    return 0.005 * (20.0 / (zoom + 0.0000000000000001))

def near_rests(lat=34.985458, lng=135.757755, zoom=1, limit=100, lonely=True):
    '''引数のlat(緯度)とlng(経度)を中心として、縦横margin*2の正方形ないにある
    レストランをTabelogテーブルから取得する
    デフォルト値は京都駅の緯度経度
    '''
    session = Session()
    margin = _get_margin(zoom)
    left, right = lng - margin, lng + margin
    bottom, top = lat - margin, lat + margin
    # lonely = u"一人で" if lonely else ""
    lonely = u"and t.situation like \"%一人で%\"" if lonely else ""
    # box = 'POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))' \
    #         % (left, bottom, right, bottom, right, top, left, top, left, bottom)
    #         # % (x+m, y-m, x-m, y-m, x-m, y+m, x+m, y+m, x+m, y-m)
    # point = 'POINT({lat} {lng})'
    # # s = session.query(Tabelog.RestaurantName, gf.wkt(Tabelog.LatLng))\
    # s = session.query(
    #         Tabelog.Rcd.label('rst_id'), Tabelog.RestaurantName, Tabelog.Category,
    #         # Tabelog.TabelogMobileUrl, Tabelog.TotalScore, Tabelog.Situation,
    #         # Tabelog.DinnerPrice, Tabelog.LunchPrice, Tabelog.Category,
    #         # Tabelog.Station, Tabelog.Address, Tabelog.Tel,
    #         # Tabelog.BusinessHours, Tabelog.Holiday,
    #         # gf.wkt(Tabelog.LatLng).label('Point'),
    #         gf.x(Tabelog.LatLng).label('lat'),
    #         gf.y(Tabelog.LatLng).label('lng'),
    #         gf.length(LineString(point.format(lat=lat, lng=lng),\
    #                 gf.wkt(Tabelog.LatLng))).label('length'),\
    #         func.round(func.avg(UserPost.difficulty)).label('difficulty'),\
    #         func.avg(UserPost.difficulty).label('raw_difficulty'))\
    #         .filter(UserPost.rst_id == Tabelog.Rcd)\
    #         .filter(Tabelog.LatLng.within(box))\
    #         .order_by('length')\
    #         .group_by(UserPost.id)\
    #         .limit(limit).all()
    #         # .order_by(gf.distance(point.format(lat=lat, lng=lng),\
    #         #     point.format(lat=gf.x(Tabelog.LatLng), lng=gf.y(Tabelog.LatLng))))\
    #         # .desc()\
    try:
        s = session.execute(\
            unicode("select t.Rcd as rst_id, t.RestaurantName, t.Category, "
            "X(t.LatLng) as lat, Y(t.LatLng) as lng, "
            "floor(avg(up.difficulty)+0.5) as difficulty,"
            "avg(up.difficulty) as raw_difficulty, "
            "GLength(GeomFromText(Concat('LineString("
            "{lat} {lng}, ', Y(t.LatLng), ' ', X(t.LatLng), ')'))) as distance "
            "from tabelog as t, user_post as up "
            "where t.Rcd = up.rst_id and MBRContains(GeomFromText('"
            "LineString({tr_lng} {tr_lat}, {bl_lng} {bl_lat})'), t.LatLng) "
            "{lonely} "   # 一人で？
            "group by up.id order by distance asc limit {limit}")\
            .format(lat=lat, lng=lng, \
            tr_lng=right, tr_lat=top, bl_lng=left, bl_lat=bottom, limit=limit,\
            lonely=lonely))
        results = [dict(result) for result in s.fetchall()]
    except Exception, e:
        print e
        session.rollback()
        results = False
    session.commit()
    session.close()
    return results

def full_info_of_near_rests(lat=34.985458, lng=135.757755, zoom=1, limit=None):
    '''引数のlat(緯度)とlng(経度)を中心として、縦横margin*2の正方形ないにある
    レストランをTabelogテーブルから取得する
    デフォルト値は京都駅の緯度経度
    '''
    margin = _get_margin(zoom)
    left, right = lng - margin, lng + margin
    bottom, top = lat - margin, lat + margin
    box = 'POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))' \
            % (left, bottom, right, bottom, right, top, left, top, left, bottom)
            # % (x+m, y-m, x-m, y-m, x-m, y+m, x+m, y+m, x+m, y-m)
    session = Session()
    # s = session.query(Tabelog.RestaurantName, gf.wkt(Tabelog.LatLng))\
    s = session.query(
            Tabelog.id, Tabelog.Rcd, Tabelog.RestaurantName,
            Tabelog.TabelogMobileUrl, Tabelog.TotalScore, Tabelog.Situation,
            Tabelog.DinnerPrice, Tabelog.LunchPrice, Tabelog.Category,
            Tabelog.Station, Tabelog.Address, Tabelog.Tel,
            Tabelog.BusinessHours, Tabelog.Holiday,
            func.round(func.avg(UserPost.difficulty)).label('difficulty'),\
            gf.wkt(Tabelog.LatLng).label('Point'))\
            .filter(Tabelog.Rcd == UserPost.rst_id)\
            .filter(Tabelog.LatLng.within(box))\
            .group_by(UserPost.id)\
            .limit(limit)
    session.commit()
    session.close()
    return s

def read_rst(rst_id):
    # 店の詳細情報取得
    session = Session()
    s = session.query(
            Tabelog.Rcd.label('rst_id'), Tabelog.RestaurantName,
            Tabelog.TabelogMobileUrl, Tabelog.TotalScore, Tabelog.Situation,
            Tabelog.DinnerPrice, Tabelog.LunchPrice, Tabelog.Category,
            Tabelog.Station, Tabelog.Address, Tabelog.Tel,
            Tabelog.BusinessHours, Tabelog.Holiday,
            gf.x(Tabelog.LatLng).label('lat'),
            gf.y(Tabelog.LatLng).label('lng'),
            func.round(func.avg(UserPost.difficulty)).label('difficulty'),\
            func.avg(UserPost.difficulty).label('raw_difficulty'))\
            .filter(Tabelog.Rcd == rst_id)\
            .filter(UserPost.rst_id == Tabelog.Rcd)\
            .group_by(UserPost.id).first()
            # gf.wkt(Tabelog.LatLng).label('Point'))\
            #         .filter('Rcd = :rcd').params(rcd=rst_id).first()
    session.commit()
    session.close()
    return s

def searce_rst(query):
    session = Session()
    s = session.query(Tabelog)

#}}}

##############################
# User#{{{
##############################

def read_user(user_id):
    '''Userテーブルからid=user_idのユーザーの情報を取得
    返り値はuserの情報
    '''
    session = Session()
    user = session.query(User.id, User.user_name, User.home_place)\
            .filter('id = :user_id')\
            .params(user_id = user_id).first()
    session.commit()
    session.close()
    return user

def create_user(user_name, home_place=None):
    '''Userテーブルに新しいユーザを追加
    返り値はそのid
    '''
    if not user_name:
        return False
    session = Session()
    now = datetime.now()
    user_name = user_name.replace('\n', '')
    new_user = User(user_name, home_place, created=now, modified=now)
    return insert_data(session, new_user)

def update_user(user_id, new_name, new_place):
    '''Userテーブルを更新
    返り値はTrue or False
    '''
    session = Session()
    now = datetime.now()
    try:
        user = session.query(User)\
                .filter('id = :user_id')\
                .params(user_id = user_id).first()
        user.user_name = new_name
        user.home_place = new_place
        user.modified = now
        session.flush()
        session.commit()
        session.close()
        return True
    except Exception, e:
        session.rollback()
        print e
        session.commit()
        session.close()
        return False

def delete_user(user_id, confirmation=False):
    '''Userテーブルからユーザーを削除
    確認(confirmation)を指定する
    '''
    if not confirmation:
        return False
    session = Session()
    try:
        user = session.query(User).filter('id = :user_id')\
                .params(user_id = user_id).first()
        session.delete(user)
        session.flush()
        session.commit()
        session.close()
        return True
    except Exception, e:
        session.rollback()
        print e
        session.commit()
        session.close()
        return False#}}}

##############################
# UserPost#{{{
##############################

def read_user_post(user_id, rst_id):
    '''user_postからuser_idとrst_idの組を持つ行を取得
    user_idが無ければ、rst_idについての組を全て取得
    '''
    session = Session()
    if user_id:
        print 'user_id is exists'
        userpost = session.query(UserPost.user_id, UserPost.rst_id, \
                UserPost.difficulty, UserPost.comment)\
                .filter('user_id = :user_id and rst_id = :rst_id')\
                .params(user_id = user_id, rst_id = rst_id)
    else:
        print 'user_id is None'
        userpost = session.query(UserPost.user_id, UserPost.rst_id, \
                UserPost.difficulty, UserPost.comment)\
                .filter('rst_id = :rst_id')\
                .params(rst_id = rst_id)
    session.commit()
    session.close()
    return userpost

def delete_user_post(user_id, rst_id):
    '''UserPostテーブルから、user_idとrst_idの組をもつ行を削除する
    '''
    if not user_id:
        return False
    session = Session()
    try:
        userpost = session.query(UserPost)\
                .filter('user_id = :user_id and rst_id = :rst_id')\
                .params(user_id = user_id, rst_id = rst_id).first()
        print userpost
        session.delete(userpost)
        session.flush()
        session.commit()
        session.close()
        return True
    except Exception, e:
        print 'delete_user_post :', e
        session.rollback()
        session.commit()
        session.close()
        return False

def insert_or_update_user_post(user_id, rst_id, difficulty, comment):
    '''UserPostテーブルにinsert or updateを行う
    そのrowのidを返す
    '''
    session = Session()
    now = datetime.now()
    userpost = _check_user_post_is_exists(session, user_id, rst_id)
    if userpost:
        print 'update user_post'
        try:
            userpost.modified = now
            userpost.difficulty = difficulty
            userpost.comment = comment
            inserted_id = userpost.id
            session.flush()
        except Exception, e:
            print e
            session.rollback()
        session.close()
    else:
        print 'create user_post'
        new_user_post = UserPost(user_id, rst_id, difficulty, comment, now, now)
        inserted_id = insert_data(session, new_user_post)
    return inserted_id

def _check_user_post_is_exists(session, user_id, rst_id):
    '''UserPostテーブルにuser_idとrst_idの組があればそのuserpostオブジェクトを、
    無ければNoneを返す
    '''
    return session.query(UserPost)\
            .filter('user_id = :user_id and rst_id = :rst_id')\
            .params(user_id=user_id, rst_id=rst_id).first()

def read_comments(rst_id):
    '''rst_idの店について、他の人のコメントを取得する
    '''
    session = Session()
    s = session.query(UserPost.comment, UserPost.difficulty, User.user_name)\
            .filter(UserPost.user_id == User.id)\
            .filter(UserPost.rst_id == rst_id)\
            .order_by(UserPost.modified.desc()).limit(10).all()
    posts = [_s._asdict() for _s in s]
    session.commit()
    session.close()
    return posts

def avg_difficult(rst_id):
    '''Tabelog.idの店について、平均のdifficultyを返す
    '''
    # rst_id = session.query(Tabelog.Rcd)\
    #         .filter('id = :id').params(id = id).first()
    if not rst_id:
        print 'no such Restaurant'
        return False
    session = Session()
    avg = session.query(func.avg(UserPost.difficulty))\
            .filter('rst_id = :rst_id').params(rst_id = rst_id).first()
    session.commit()
    session.close()
    return float(avg[0]) if avg[0] else False
#}}}

##############################
# Title#{{{
##############################
def create_title(rank, name, requirement, stamp):
    '''Titleを作成
    rank:プラチナとか
    requirement：条件文
    stamp:スタンプ名
    '''
    session =  Session()
    now = datetime.now()
    new_title = Title(rank, name, requirement, stamp, created=now, modified=now)
    return insert_data(session, new_title)

def read_title(title_id):
    session = Session()
    title = session.query(Title.id, User.user_name, User.home_place)\
            .filter(Title.id == title_id).first()
    session.commit()
    session.close()
    return title

def update_title(title_id, rank, name, requirement, stamp):
    now = datetime.now()
    session = Session()
    title = session.query(Title).filter(Title.id == title_id)
    title.rank = rank
    title.name = name
    title.requirement = requirement
    title.stamp = stamp
    title.modified = now
    try:
        session.flush()
        session.commit()
    except Exception ,e:
        session.rollback()
        print e
        session.commit()
        session.close()
        return False
    updated_id = title.id
    session.close()
    return updated_id


def insert_or_update_titles():
    titles = open("titles.txt", 'r').read().strip().split("\n")
    for id, title in enumerate(titles):
        rank, name, requirement, stamp = title.split(',')
        _insert_or_update_title(id, rank, name, requirement, stamp)
    return True

def _insert_or_update_title(id=None, rank=None, name=None, \
                                        requirement=None, stamp=None):
    '''称号の運営用
    新しく称号を追加、更新するために使う
    '''
    now = datetime.now()
    session = Session()
    if not name or not requirement:
        print '称号名と取得条件を入力してください'
        return False
    title = session.query(Title)\
            .filter(Title.id == id)\
            .limit(1).first()
    try:
        if title:
            title.rank = rank
            title.stamp = stamp
            title.modified = now
            print 'title update',
        else:
            title = Title(id, rank, name, requirement, stamp, now, now)
            session.add(title)
            print 'title insert',
        print name
        session.flush()
        session.commit()
        session.close()
        return True
    except Exception, e:
        print e
        session.rollback()
        session.commit()
        session.close()
        return False

def judge_acquired_title(user_id):
    '''user_idでそのユーザーが取得している称号の名前を返す
    '''
    jt = JudgeTitle(user_id)
    acquired_titles = jt.fetch_title_id()
    # acquired_titles = jt.fetch_title_name()
    return acquired_titles


def delete_title(id):
    session = Session()
    try:
        title = session.query(Title).filter(Title.id == id).first()
        print title
        session.delete(title)
        session.flush()
        session.commit()
        session.close()
        return True
    except Exception, e:
        print 'delete_user_post :', e
        session.rollback()
        session.commit()
        session.close()
        return False#}}}

##############################
# UserStats#{{{
##############################

def create_userstats(user_id, total, sequence, level_1, level_2, level_3,\
        level_4, level_5, sakyo, ukyo, kita, kamigyo, shimogyo, nakagyo,\
        higashiyama, yamashina, saikyo, minami, fushimi, already_acquire,\
        created, modified):
    '''userstatsを作成
    requirement：条件文
    '''
    session =  Session()
    now = datetime.now()
    new_userstats = UserStats(user_id, total, sequence, \
            level_1, level_2, level_3, level_4, level_5, \
            sakyo, ukyo, kita, kamigyo, shimogyo, nakagyo,\
            higashiyama, yamashina, saikyo, minami, fushimi, \
            already_acquire, created=now, modified=now)
    return insert_data(session, new_userstats)

def read_userstats(user_id):
    session = Session()
    userstats = UserStats(\
            UserStats.user_id, UserStats.total, UserStats.sequence, \
            UserStats.level_1, UserStats.level_2, UserStats.level_3,
            UserStats.level_4, UserStats.level_5, \
            UserStats.sakyo, UserStats.ukyo, UserStats.kita, UserStats.kamigyo,
            UserStats.shimogyo, UserStats.nakagyo,\
            UserStats.higashiyama, UserStats.yamashina, UserStats.saikyo,
            UserStats.minami, UserStats.fushimi, UserStats.already_acquire,
            UserStats.created, UserStats.modified)\
            .filter('user_id = :user_id')\
            .params(user_id = user_id).first()
    session.commit()
    session.close()
    return userstats

def update_userstats(\
        user_id, total=None, sequence=None,
        level_1=None, level_2=None, level_3=None, level_4=None, level_5=None, \
        sakyo=None, ukyo=None, kita=None, kamigyo=None, shimogyo=None, \
        nakagyo=None, higashiyama=None, yamashina=None, saikyo=None, \
        minami=None, fushimi=None, already_acquire=None):
    now = datetime.now()
    session = Session()
    userstats = session.query(UserStats).filter(user_id=user_id).first()
    if total:
        userstats.total = total
    if sequence:
        userstats.sequence = sequence
    if level_1:
        userstats.level_1 = level_1
    if level_2:
        userstats.level_2 = level_2
    if level_3:
        userstats.level_3 = level_3
    if level_4:
        userstats.level_4 = level_4
    if level_5:
        userstats.level_5 = level_5
    if sakyo:
        userstats.sakyo = sakyo
    if ukyo:
        userstats.ukyo = ukyo
    if kita:
        userstats.kita = kita
    if kamigyo:
        userstats.kamigyo = kamigyo
    if shimogyo:
        userstats.shimogyo = shimogyo
    if nakagyo:
        userstats.nakagyo = nakagyo
    if higashiyama:
        userstats.higashiyama = higashiyama
    if yamashina:
        userstats.yamashina = yamashina
    if saikyo:
        userstats.saikyo = saikyo
    if minami:
        userstats.minami = minami
    if fushimi:
        userstats.fushimi = fushimi
    if already_acquire:
        userstats.already_acquire = already_acquire
    userstats.modified = now
    try:
        session.flush()
        session.commit()
    except Exception ,e:
        session.rollback()
        print e
        session.commit()
        session.close()
        return False
    updated_id = userstats.id
    session.close()
    return updated_id

def delete_userstats(user_id):
    session = Session()
    try:
        userstats = session.query(UserStats).filter(user_id = user_id).first()
        print userstats
        session.delete(userstats)
        session.flush()
        session.commit()
        session.close()
        return True
    except Exception, e:
        print 'delete_userstats :', e
        session.rollback()
        session.commit()
        session.close()
        return False
#}}}
