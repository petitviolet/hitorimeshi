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



