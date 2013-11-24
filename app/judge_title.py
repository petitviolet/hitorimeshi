# -*- encoding:utf-8 -*-

from Table import Session, Tabelog, UserPost, UserStats, Title
from sqlalchemy import func
import re
import datetime

class JudgeTitle(object):
    def __init__(self, user_id):
        self.user_id = user_id
        session = Session()
        try:
            self.stats = session.query(UserStats.total, UserStats.sequence,
                    UserStats.level_1, UserStats.level_2, UserStats.level_3,
                    UserStats.level_4, UserStats.level_5, UserStats.sakyo,
                    UserStats.ukyo, UserStats.kita, UserStats.kamigyo,
                    UserStats.shimogyo, UserStats.nakagyo, UserStats.higashiyama,
                    UserStats.yamashina, UserStats.saikyo, UserStats.minami,
                    UserStats.fushimi, UserStats.already_acquire)\
                            .filter(UserStats.user_id == user_id).first()._asdict()
        except:
            print 'rollback'
            session.rollback()
        self.acquire = set()
        session.commit()
        session.close()

    def total(self):
        '''totalのぼっち飯回数が各条件を超えていたら、
        その称号のtitle.idをself.acquireに追加する
        idを決め打ちしてるから注意
        '''
        total = self.stats['total']
        conds = [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, \
                250, 300, 400, 500, 1000]
        number = len(conds)
        for idx, cond in enumerate(conds):
            print number, idx
            if total >= cond:
                self.acquire.add(number - idx)
            else:
                break
        return True

    def ku(self):
        session = Session()
        section_req = re.compile("(.*)区.*?(\d+)件.*")
        some_sec_req = re.compile("京都(\d+)区.*")
        id_reqs = session.query(Title.id, Title.requirement)\
                .filter(Title.requirement.like("%区%")).all()
        session.commit()
        session.close()
        kyoto_ku_counts = 0
        kus = ['sakyo', 'ukyo', 'kita', 'kamigyo', 'shimogyo', 'nakagyo',\
                'higashiyama', 'yamashina', 'saikyo', 'minami', 'fushimi']
        kus_dic = {'左京': 'sakyo', '右京': 'ukyo', '北': 'kita',
                    '上京': 'kamigyo', '下京': 'shimogyo', '中京': 'nakagyo',
                    '東山': 'higashiyama', '山科': 'yamashina',
                    '南': 'minami', '伏見': 'fushimi', '西京': 'saikyo'}
        for _ku in kus:
            if self.stats[_ku]:
                kyoto_ku_counts += 1
        for id, req in id_reqs:
            try:
                sec = section_req.findall(req)[0]
            except:
                sec = None
            try:
                some_secs = some_sec_req.findall(req)[0]
            except:
                some_secs = None
            if some_secs:
                if kyoto_ku_counts >= int(some_secs):
                    self.acquire.add(id)
                    print id
            elif sec:
                _ku, _req = sec
                if self.stats[kus_dic[_ku]] >= int(_req):
                    self.acquire.add(id)
                    print id
        return True

    def fetch_title_name(self):
        session = Session()
        self.total()
        self.ku()
        title_names = []
        try:
            for title_id in self.acquire:
                _title = session.query(Title.name)\
                        .filter(Title.id == title_id).first().name
                title_names.append(_title)
        except Exception, e:
            print e
            session.rollback()
        session.commit()
        session.close()
        return title_names
