# -*- encoding:utf-8 -*-

from Table import Session, Tabelog, User, UserPost
import geoalchemy.functions as gf
from sqlalchemy import func
from urllib import urlopen
import json
from datetime import datetime

def geo_coding(landmark):
    url = 'http://maps.googleapis.com/maps/api/geocode/json?address={landmark}&sensor=true'
    geo_json = json.load(urlopen(url.format(landmark=landmark)))
    latlng = geo_json['results'][0]['geometry']['location']
    result = {'lat':latlng['lat'], 'lng':latlng['lng']}
    return result

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
            gf.wkt(Tabelog.LatLng).label('Point'))\
                    .filter(where)
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
    session.close()
    return s

def _get_margin(zoom=1.0):
    return 0.005 * (20.0 / (zoom + 0.0000000000000001))

def near_rests(lat=34.985458, lng=135.757755, zoom=1, limit=None):
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
            gf.wkt(Tabelog.LatLng).label('Point'))\
            .filter(Tabelog.LatLng.within(box))\
            .limit(limit)
    session.close()
    return s

def read_user(user_id):
    '''Userテーブルからid=user_idのユーザーの情報を取得
    返り値はuserの情報
    '''
    session = Session()
    user = session.query(User.id, User.user_name, User.home_place)\
            .filter('id = :user_id')\
            .params(user_id = user_id).first()
    session.close()
    return user

def create_user(user_name, home_place):
    '''Userテーブルに新しいユーザを追加
    返り値はそのid
    '''
    session = Session()
    now = datetime.now()
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
        session.close()
        return False

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
        print 'update'
        try:
            userpost.modified = now
            userpost.difficulty = difficulty
            userpost.comment = comment
            inserted_id = userpost.id
            session.flush()
            session.commit()
        except Exception, e:
            print e
            session.rollback()
        session.close()
    else:
        print 'create'
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
        session.close()
        return False
    inserted_id = new_obj.id
    session.close()
    return inserted_id

def avg_difficult(id):
    '''Tabelog.idの店について、平均のdifficultyを返す
    '''
    session = Session()
    rst_id = session.query(Tabelog.Rcd)\
            .filter('id = :id').params(id = id).first()
    if not rst_id:
        print 'no such Restaurant'
        session.close()
        return False
    avg = session.query(func.avg(UserPost.difficulty))\
            .filter('rst_id = :rst_id').params(rst_id = rst_id[0]).first()
    session.close()
    return float(avg[0]) if avg[0] else False

