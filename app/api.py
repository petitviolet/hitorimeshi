#!/usr/local/bin/python
# -*- encoding:utf-8 -*-
'''アプリ用API
あらゆるアクセスにbasic認証を必要とする'''

from simplejson import dumps, loads
from functools import wraps
import db_funcs as df
from flask import Flask, jsonify, request, abort
from logger import config_logger
from basic_auth import requires_auth
from secret import HOST
from flask.ext.cache import Cache

__version__ = 1.0

# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

def create_app():
    # app = Flask(__name__)
    app = Flask('hitorimeshi')
    config_logger(app)
    return app

cache = Cache()
app = create_app()
cache.init_app(app, config={'CACHE_TYPE': 'simple'})

# basic認証
@app.before_request
@requires_auth
def before_request():
    pass

def consumes(content_type):
    '''Content-Typeをapplication/jsonに変更するために使う
    '''
    def _consumes(function):
        @wraps(function)
        def __consumes(*argv, **keywords):
            if request.headers['Content-Type'] != content_type:
                abort(400)
            return function(*argv, **keywords)
        return __consumes
    return _consumes

def _to_serializable_dict(result_obj):
    '''index用
    '''
    result_set = result_obj.order_by(df.Tabelog.TotalScore.desc()).all()
    try:
        return len(result_set), [result._asdict() for result in result_set]
    except Exception, e:
        print e
        return len(result_set), False

def _check_form(forms, tokens):
    '''request.formにtokenが存在するかどうかを確かめ、型変換、エンコードを行う
    tokensは{key: 型(int or float or str)}
    '''
    result = {}
    for k, t in tokens.iteritems():
        value = forms.get(k)
        try:
            if t == 'int':
                value = int(value)
            elif t == 'float':
                value = float(value)
            elif t == 'str':
                value = value.encode('utf-8')
        except Exception, e:
            # print e
            value = None
        result[k] = value
    return result

# @app.route('/', methods=['GET'])
# @app.route('/hitorimeshi/api', methods=['GET'])
@app.route('/', methods=['POST'])
def index():
    # ユーザ一覧からレスポンスを作る
    response = jsonify({'name': request.args.get('name')})
    index_info = df.near_rests(zoom=10)
    index_count, index_data = _to_serializable_dict(index_info)
    response = jsonify({'count': index_count, 'result' : index_data})
    # ステータスコードは OK (200)
    # response.status_code = 200
    return response

##############################
# Tabelogテーブル
##############################
@app.route('/near_rst', methods=['POST'])
def near_rsts():
    '''(lat, lng)に近い店舗をzoomにあわせてlimit件取得する
    postメソッドでzoomとlatとlngとlimit
    '''
    # near_rests(lat=34.985458, lng=135.757755, zoom=1):
    if len(request.form) == 0:
        response = jsonify({'result': False})
        response.status_code = 500
    else:
        _type = {'zoom': 'float', 'lat': 'float', 'lng': 'float', 'limit': 'int'}
        values = _check_form(request.form, _type)
        zoom = values['zoom']
        lat = values['lat']
        lng = values['lng']
        limit = values['limit']
        rsts = get_near_rsts(zoom=zoom, lat=lat, lng=lng, limit=limit)
        response = jsonify({'result': rsts})
        response.status_code = 200 if rsts else 418
    return response

@cache.memoize(timeout=15)
def get_near_rsts(zoom, lat, lng, limit):
    '''(lat, lng)に近い店舗をzoomにあわせてlimit件取得する
    '''
    limit = limit if limit else 100
    rsts = df.near_rests(lat=lat, lng=lng, zoom=zoom, limit=limit).all()
    rsts = [rst._asdict() for rst in rsts] if rsts else None
    return rsts

# test
@app.route('/full_info_of_near_rst', methods=['POST'])
def test_near_rsts():
    '''(lat, lng)に近い店舗をzoomにあわせてlimit件取得する
    postメソッドでzoomとlatとlngとlimit
    '''
    # near_rests(lat=34.985458, lng=135.757755, zoom=1):
    if len(request.form) == 0:
        response = jsonify({'result': False})
        response.status_code = 500
    else:
        _type = {'zoom': 'float', 'lat': 'float', 'lng': 'float', 'limit': 'int'}
        values = _check_form(request.form, _type)
        zoom = values['zoom']
        lat = values['lat']
        lng = values['lng']
        limit = values['limit']
        rsts = get_full_info_of_near_rsts(zoom=zoom, lat=lat, lng=lng, limit=limit)
        response = jsonify({'result': rsts})
        response.status_code = 200 if rsts else 418
    return response

@cache.memoize(timeout=15)
def get_full_info_of_near_rsts(zoom, lat, lng, limit):
    '''(lat, lng)に近い店舗をzoomにあわせてlimit件取得する
    '''
    limit = limit if limit else 100
    rsts = df.full_info_of_near_rests(lat=lat, lng=lng, zoom=zoom, limit=limit).all()
    rsts = [rst._asdict() for rst in rsts] if rsts else None
    return rsts
####

@app.route('/read_rst', methods=['POST'])
def read_rst():
    '''rcd(rst_id)を渡してその店舗の詳細情報を得る
    postメソッドで、rst_id
    '''
    _type = {'rst_id': 'int'}
    values = _check_form(request.form, _type)
    rst_id = values['rst_id']
    rst_info = get_rst_info(rst_id)
    response = jsonify({'result': rst_info})
    response.status_code = 200
    return response

@cache.memoize(timeout=15)
def get_rst_info(rst_id):
    '''dbにアクセスするもので、cacheを使う
    '''
    rst_info = df.read_rst(rst_id)
    return rst_info._asdict() if rst_info else None

##############################
# Userテーブル
##############################

@app.route('/create_user', methods=['POST'])
# @consumes('application/json')
def create_user():
    '''Userにユーザーを作成
    postメソッドでnameとhome
    '''
    _type = {'name': 'str', 'home': 'str'}
    values = _check_form(request.form, _type)
    user_name = values['name']
    home_place = values['home']
    # user_name = request.form.get('name').encode('utf-8')
    # home_place = request.form.get('home').encode('utf-8')
    inserted_id = df.create_user(user_name, home_place)
    response = jsonify({'user_id': inserted_id})
    response.status_code = 201 if inserted_id else 418
    return response

@app.route('/read_user', methods=['POST'])
def read_user():
    '''Userのユーザ情報取得
    postメソッドでuser_id
    '''
    _type = {'user_id': 'int'}
    values = _check_form(request.form, _type)
    user_id = values['user_id']
    # print request.__dict__
    if not user_id:
        response = jsonify({'result': False})
        response.status_code = 418
        return response
    user = df.read_user(int(user_id))
    user = user._asdict() if user else None
    # response = jsonify(user)
    response = jsonify({'result': user})
    response.status_code = 200
    return response

@app.route('/update_user', methods=['PUT'])
# @consumes('application/json')
def update_user():
    '''Userのユーザーを更新
    putメソッドでuser_idとnew_nameとnew_home
    '''
    # user_id = int(request.form.get('user_id'))
    # new_name = request.form.get('new_name').encode('utf-8')
    # new_place = request.form.get('new_home').encode('utf-8')
    _type = {'user_id': 'int', 'new_name': 'str', 'new_home': 'str'}
    values = _check_form(request.form, _type)
    user_id = values['user_id']
    new_name = values['new_name']
    new_place = values['new_home']
    success = df.update_user(user_id, new_name, new_place)
    response = jsonify({'update': success})
    response.status_code = 201 if success else 418
    return response

@app.route('/delete_user', methods=['DELETE'])
def delete_user():
    '''Userからユーザーを削除
    deleteメソッドでuser_idとconfirmation
    '''
    _type = {'user_id': 'int'}
    values = _check_form(request.form, _type)
    user_id = values['user_id']
    confirmation = request.form.get('confirmation')
    success = df.delete_user(user_id, confirmation=confirmation)
    response = jsonify({'delete': success})
    response.status_code = 200 if success else 418
    return response

@app.route('/situation', methods=['GET'])
def get_situation():
    '''/situation?situation=一人
    とかでそのsituationにあった店リストを返す
    '''
    situation = request.args.get('situation')
    if not situation:
        return False
    found_user = df.get_situation(situation.encode('utf-8'))
    # レスポンスオブジェクトを作る
    count, result = _to_serializable_dict(found_user)
    response = jsonify({'count': count, 'result': result})
    # ステータスコードは Created (201)
    response.status_code = 200
    return response

##############################
# UserPostテーブルのCRUD
##############################

@app.route('/post', methods=['POST'])
# def insert_or_update_user_post(user_id, rst_id, difficulty, comment):
def create_or_update_post():
    '''UserPostにデータを作成or更新
    postメソッドでuser_idとrst_idとdifficultyとcomment
    '''
    _type = {'user_id': 'int', 'rst_id': 'int', \
                    'difficulty': 'float', 'comment': 'str'}
    values = _check_form(request.form, _type)
    user_id = values['user_id']
    rst_id = values['rst_id']
    difficulty = values['difficulty']
    comment = values['comment']

    # user_id = int(request.form.get('user_id'))
    # rst_id = int(request.form.get('rst_id'))
    # difficulty = float(request.form.get('difficulty'))
    # comment = request.form.get('comment').encode('utf-8')
    inserted_id = df.insert_or_update_user_post(\
            user_id, rst_id, difficulty, comment)
    response = jsonify({'user_post_id': inserted_id})
    response.status_code = 201 if inserted_id else 418
    return response

@app.route('/read_post', methods=['POST'])
def read_post():
    '''UserPostのデータを取得
    postメソッドでuser_idとrst_id
    '''
    _type = {'user_id': 'int', 'rst_id': 'int'}
    values = _check_form(request.form, _type)
    user_id = values['user_id']
    rst_id = values['rst_id']

    # user_id = int(request.form.get('user_id'))
    # rst_id = int(request.form.get('rst_id'))
    userpost = df.read_user_post(user_id, rst_id)\
            .order_by(df.UserPost.modified).all()
    # DECIMAL型をfloatに変換するため、simplejson.dumpsを使う
    try:
        response = jsonify(\
                loads(dumps({'user_post': [up._asdict() for up in userpost]})))
    except Exception, e:
        print e
        response = jsonify({'user_post': False})
    response.status_code = 200
    return response

@app.route('/delete_post', methods=['DELETE'])
def delete_post():
    '''UserPostからデータを削除
    deleteメソッドでuser_idとrst_id
    '''
    _type = {'user_id': 'int', 'rst_id': 'int'}
    values = _check_form(request.form, _type)
    user_id = values['user_id']
    rst_id = values['rst_id']
    # user_id = int(request.form.get('user_id'))
    # rst_id = int(request.form.get('rst_id'))
    success = df.delete_user_post(user_id, rst_id)
    response = jsonify({'delete_user_post': success})
    response.status_code = 200 if success else 418
    return response


# @app.route('/<int:user_id>', methods=['DELETE'])
# def delete(user_id):
#     # リクエストされたパスと ID を持つユーザを探す
#     _get_user(user_id)
#     # ユーザがいれば削除する
#     users.pop(user_id)
#     # レスポンスオブジェクトを作る
#     response = Response()
#     # ステータスコードは NoContent (204)
#     response.status_code = 204
#     return response

if __name__ == '__main__':
    app.debug = True
    # app.run()
    app.host = HOST
    app.run(host=HOST)
