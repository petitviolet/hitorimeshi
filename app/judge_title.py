# -*- encoding:utf-8 -*-

from Table import Session, Tabelog, UserPost, UserStats
from sqlalchemy import func
import re
import datetime

class JudgeTitle(object):
    def __init__(self, user_id):
        self.user_id = user_id
        session = Session()
        self.stats = session.query(UserStats.total, UserStats.sequence,
                UserStats.level_1, UserStats.level_2, UserStats.level_3,
                UserStats.level_4, UserStats.level_5, UserStats.sakyo,
                UserStats.ukyo, UserStats.kita, UserStats.kamigyo,
                UserStats.shimogyo, UserStats.nakagyo, UserStats.higashiyama,
                UserStats.yamashina, UserStats.saikyo, UserStats.minami,
                UserStats.fushimi, UserStats.already_acquire)\
                        .filter(UserStats.id == user_id).first()._asdict()
        self.acquire = []
        session.commit()
        session.close()

    def total(self):
        '''totalのぼっち飯回数が各条件を超えていたら、
        その称号のtitle.idをself.acquireに追加する
        '''
        total = self.stats['total']
        conds = [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, \
                250, 300, 400, 500, 1000]
        number = len(conds) - 1
        for idx, cond in enumerate(conds):
            if total >= cond:
                self.acquire.append(number - idx)
            else:
                break
        return True

    def fetch_title_id(self):
        pass

