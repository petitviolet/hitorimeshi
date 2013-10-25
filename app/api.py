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

__version__ = 1.0

# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

def create_app():
    # app = Flask(__name__)
    app = Flask('hitorimeshi')
    config_logger(app)
    return app

app = create_app()
# basic認証
@app.before_request
@requires_auth
def before_request():
    pass

def consumes(content_type):
    '''謎のラッパー
    '''
    def _consumes(function):
        @wraps(function)
        def __consumes(*argv, **keywords):
            if request.headers['Content-Type'] != content_type:
                abort(400)
            return function(*argv, **keywords)
        return __consumes
    return _consumes

def to_serializable_dict(result_obj):
    '''index用
    '''
    result_set = result_obj.order_by(df.Tabelog.TotalScore.desc()).all()
    try:
        return len(result_set), [result._asdict() for result in result_set]
    except Exception, e:
        print e
        return len(result_set), False


# @app.route('/', methods=['GET'])
# @app.route('/hitorimeshi/api', methods=['GET'])
@app.route('/', methods=['GET'])
def index():
    # ユーザ一覧からレスポンスを作る
    response = jsonify({'name': request.args.get('name')})
    index_info = df.near_rests(zoom=10)
    index_count, index_data = to_serializable_dict(index_info)
    response = jsonify({'count': index_count, 'result' : index_data})
    # ステータスコードは OK (200)
    # response.status_code = 200
    return response

##############################
# Tabelogテーブル
##############################
@app.route('/near_rst', methods=['GET'])
def near_rests():
    # near_rests(lat=34.985458, lng=135.757755, zoom=1):
    print 'request :', request.form
    if len(request.form) == 0:
        response = jsonify({'result': False})
        response.status_code = 500
    else:
        zoom = request.form.get('zoom')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        limit = request.form.get('limit')
        limit = int(limit) if limit else 100
        rsts = df.near_rests(lat=float(lat), lng=float(lng), \
                zoom=float(zoom), limit=limit).all()
        rsts = [rst._asdict() for rst in rsts] if rsts else None
        response = jsonify({'result': rsts})
        response.status_code = 200 if rsts else 418
    return response


##############################
# Userテーブル
##############################

@app.route('/create_user', methods=['POST'])
# @consumes('application/json')
def create_user():
    '''Userにユーザーを作成
    postメソッドでnameとhome
    '''
    user_name = request.form.get('name')
    home_place = request.form.get('home')
    inserted_id = df.create_user(user_name, home_place)
    response = jsonify({'user_id': inserted_id})
    response.status_code = 201 if inserted_id else 418
    return response

@app.route('/read_user', methods=['GET'])
def read_user():
    '''Userのユーザ情報取得
    getメソッドでuser_id
    '''
    user_id = request.form.get('user_id')
    user = df.read_user(user_id)
    user = user._asdict() if user else None
    response = jsonify({'result': user})
    response.status_code = 200
    return response

@app.route('/update_user', methods=['PUT'])
# @consumes('application/json')
def update_user():
    '''Userのユーザーを更新
    putメソッドでuser_idとnew_nameとnew_home
    '''
    user_id = request.form.get('user_id')
    new_name = request.form.get('new_name')
    new_place = request.form.get('new_home')
    success = df.update_user(user_id, new_name, new_place)
    response = jsonify({'update': success})
    response.status_code = 201 if success else 418
    return response

@app.route('/delete_user', methods=['DELETE'])
def delete_user():
    '''Userからユーザーを削除
    deleteメソッドでuser_idとconfirmation
    '''
    user_id = request.form.get('user_id')
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
    count, result = to_serializable_dict(found_user)
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
    Postメソッドでuser_idとrst_idとdifficultyとcomment
    '''
    user_id = request.form.get('user_id')
    rst_id = request.form.get('rst_id')
    difficulty = request.form.get('difficulty')
    comment = request.form.get('comment')
    inserted_id = df.insert_or_update_user_post(\
            user_id, rst_id, difficulty, comment)
    response = jsonify({'user_post_id': inserted_id})
    response.status_code = 201 if inserted_id else 418
    return response

@app.route('/read_post', methods=['GET'])
def read_post():
    '''UserPostのデータを取得
    Getメソッドでuser_idとrst_id
    '''
    user_id = request.form.get('user_id')
    rst_id = request.form.get('rst_id')
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
    user_id = request.form.get('user_id')
    rst_id = request.form.get('rst_id')
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
