# -*- encoding:utf-8 -*-

from Table import Session, Tabelog, UserPost, UserStats
from sqlalchemy import func
import re
from datetime import datetime

ADDRESS_PARSER = re.compile(r'京都市(.+)区')
DAYS = 30  # sequenceを計算する日数

class Update_UserStats(object):
    '''UserPostに変更があったとき、UserStatsを更新する
    '''
    def __init__(self, userid, rstid):
        self.rstid = rstid
        self.userid = userid

    def _parse_ku(self, address):
        '''addressからxx区を抜き出す
        '''
        try:
            ku = ADDRESS_PARSER.findall(address)[0]
        except TypeError:
            print 'address => ' + address
            return None
        return ku

    def _get_tabelog_from_rstid(self):
        '''rstidを使って難易度とaddressを取得
        '''
        session = Session()
        try:
            info = session.query(func.avg(UserPost.difficulty).label('difficulty'),\
                    Tabelog.Address.label('address'))\
                    .filter(UserPost.rst_id == self.rstid)\
                    .filter(Tabelog.Rcd == self.rstid).first()
            session.commit()
            session.close()
        except Exception ,e:
            session.rollback()
            print e
            session.commit()
            session.close()
            return False
        return info._asdict();

    def _arrange_info(self, info):
        '''self._get_tabelog_from_rstid()の結果を辞書形式に変換
        '''
        info['difficulty'] = int(round(info['difficulty']))
        info['ku'] = self._parse_ku(info['address'])
        del info['address']
        return info

    def fetch_tabelog_info(self):
        '''rstidで情報取得
        '''
        info = self._get_tabelog_from_rstid()
        return self._arrange_info(info)

    def _get_user_posts(self):
        '''useridでUserPostから変更日時を取得
        '''
        session = Session()
        try:
            posts = session.query(\
                    # UserPost.modified, UserPost.difficulty, UserPost.rst_id)\
                    UserPost.modified)\
                    .filter(UserPost.user_id == self.userid)\
                    .order_by(UserPost.modified).limit(DAYS).all()
            session.commit()
            session.close()
        except:
            session.rollback()
            session.commit()
            session.close()
            return False
        return posts

    def _calc_sequence(self, posts):
        '''連続でぼっち飯した日数をカウント
        '''
        sequence = 1
        count = len(posts)
        for i in xrange(1, count):
            if (posts[i].modified - posts[i-1].modified).days <= 1:
                sequence += 1
            else:
                break
        return sequence

    def fetch_userpost_info(self):
        '''useridでUserPostから連続ぼっち飯日数を取得
        '''
        posts = self._get_user_posts()
        sequence = self._calc_sequence(posts)
        return {'sequence': sequence}

    def update_stats(self):
        '''UserStatsをupdateする
        '''
        result = {}
        result.update(self.fetch_userpost_info())
        result.update(self.fetch_tabelog_info())
        print result
        session = Session()
        now = datetime.now()
        is_add = False
        try:
            userstats = session.query(UserStats)\
                        .filter(UserStats.user_id == self.userid).limit(1).first()
            if not userstats:
                userstats = UserStats(self.userid, *([0] * 21))
                userstats.created = now
                is_add = True
            userstats.total += 1
            userstats.sequence = result['sequence']
            # xx区のupdate#{{{
            ku = result['ku']
            if ku == '左京':
                userstats.sakyo += 1
            elif ku == '右京':
                userstats.ukyo += 1
            elif ku == '北':
                userstats.kita += 1
            elif ku == '上京':
                userstats.kamigyo += 1
            elif ku == '下京':
                userstats.shimogyo += 1
            elif ku == '中京':
                userstats.nakagyo += 1
            elif ku == '東山':
                userstats.higashiyama += 1
            elif ku == '山科':
                userstats.yamashina += 1
            elif ku == '西京':
                userstats.saikyo += 1
            elif ku == '南':
                userstats.minami += 1
            elif ku == '伏見':
                userstats.fushimi += 1
            else:
                raise Exception('kuがおかしい :' + ku)#}}}
            # level_xのupdate#{{{
            difficulty = result['difficulty']
            if difficulty == 1:
                userstats.level_1 += 1
            elif difficulty == 2:
                userstats.level_2 += 1
            elif difficulty == 3:
                userstats.level_3 += 1
            elif difficulty == 4:
                userstats.level_4 += 1
            elif difficulty == 5:
                userstats.level_5 += 1
            else:
                raise Exception('difficultyがおかしい :' + difficulty)#}}}
            userstats.modified = now
            if is_add:
                session.add(userstats)
            session.flush()
            session.commit()
            return True
        except Exception as e:
            print e
            session.rollback()
            session.commit()
            session.close()
            return False

