# -*- encoding:utf-8 -*-
from sqlalchemy import Column, Integer, String, Text, ForeignKey,\
        create_engine, MetaData, DECIMAL, DATETIME, exc, event, Index
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy import GeometryColumn, Point
from geoalchemy.mysql import MySQLComparator
from datetime import datetime
from secret import user, passwd, host, db
from sqlalchemy.pool import Pool


# engine = create_engine('mysql://hitorimeshi:sadp2013@localhost/hitorimeshi', \
engine = create_engine('mysql://{user}:{passwd}@{host}/{db}'\
        .format(user=user, passwd=passwd, host=host, db=db),\
        encoding='utf-8', echo=False, pool_size=15, pool_recycle=3600, \
        max_overflow=0, echo_pool=True)
Session = scoped_session(sessionmaker(\
        autocommit=False, autoflush=False, bind=engine))
# sessionはローカル変数、Sessionはグローバル変数として扱う
# session = Session()
metadata = MetaData(engine)
Base = declarative_base()
Base.query = Session.query_property()

TAGNAMES = ['Rcd', 'RestaurantName', 'TabelogUrl', 'TabelogMobileUrl',\
'TotalScore', 'TasteScore', 'ServiceScore', 'MoodScore', 'Situation', \
'DinnerPrice', 'LunchPrice', 'Category', 'Station', 'Address', 'Tel', \
'BusinessHours', 'Holiday', 'LatLng']


@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
    # optional - dispose the whole pool
    # instead of invalidating one at a time
    # connection_proxy._pool.dispose()
    # raise DisconnectionError - pool will try
    # connecting again up to three times before raising.
        raise exc.DisconnectionError()
    cursor.close()


class Tabelog(Base):
    __tablename__ = 'tabelog'
    __table_args__ = {'mysql_engine': 'MyISAM'}
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    Rcd = Column('Rcd', Integer, unique=True, index=True)
    RestaurantName = Column('RestaurantName', String(64))
    TabelogUrl = Column('TabelogUrl', String(255))
    TabelogMobileUrl = Column('TabelogMobileUrl', String(255))
    TotalScore = Column('TotalScore', String(255))
    TatalScore = Column('TasteScore', String(8))
    ServiceScore = Column('ServiceScore', String(8))
    MoodScore = Column('MoodScore', String(8))
    Situation = Column('Situation', Text)
    DinnerPrice = Column('DinnerPrice', String(128))
    LunchPrice = Column('LunchPrice', String(128))
    Category = Column('Category', String(64))
    Station = Column('Station', String(128))
    Address = Column('Address', Text)
    Tel = Column('Tel', String(32))
    BusinessHours = Column('BusinessHours', String(255))
    Holiday = Column('Holiday', Text)
    LatLng = GeometryColumn('LatLng', Point(dimension=2, srid=4326),\
            nullable=False, comparator=MySQLComparator)
    user_post = relationship('UserPost')
    def __init__(self, Rcd, RestaurantName, TabelogUrl, TabelogMobileUrl, \
                TotalScore, TasteScore, ServiceScore, MoodScore, Situation, \
                DinnerPrice, LunchPrice, Category, Station, Address, Tel, \
                BusinessHours, Holiday, LatLng):
        # self.id = id
        self.Rcd = Rcd
        self.RestaurantName = RestaurantName
        self.TabelogUrl = TabelogUrl
        self.TabelogMobileUrl = TabelogMobileUrl
        self.TotalScore = TotalScore
        self.TatalScore = TasteScore
        self.ServiceScore = ServiceScore
        self.MoodScore = MoodScore
        self.Situation = Situation
        self.DinnerPrice = DinnerPrice
        self.LunchPrice = LunchPrice
        self.Category = Category
        self.Station = Station
        self.Address = Address
        self.Tel = Tel
        self.BusinessHours = BusinessHours
        self.Holiday = Holiday
        self.LatLng = LatLng

    def __repr__(self):
        return "<Tabelog>(Rcd:{rcd}, RestaurantName:{rn})"\
                .format(rcd=self.Rcd, rn=self.RestaurantName) #, latlng=self.LatLng)

class User(Base):
    __tablename__ = 'user'
    __table_args__ = {'mysql_engine': 'MyISAM'}
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    user_name = Column('user_name', String(32))
    home_place = Column('home_place', String(255))
    user_post = relationship('UserPost')
    created = Column('created', DATETIME, default=datetime.now, nullable=False)
    modified = Column('modified', DATETIME, default=datetime.now, nullable=False)
    def __init__(self, user_name, home_place, created, modified):
        # self.id = id
        self.user_name = user_name
        self.home_place = home_place
        self.created = created
        self.modified = modified

    def __repr__(self):
        return "<User>(user_name:{un}, home_place:{hp})"\
                .format(un=self.user_name, hp=self.home_place)

class UserPost(Base):
    __tablename__ = 'user_post'
    __table_args__ = {'mysql_engine': 'MyISAM'}
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    user_id = Column('user_id', Integer, ForeignKey('user.id'))
    rst_id = Column('rst_id', Integer, ForeignKey('tabelog.Rcd'))
    difficulty = Column('difficulty', DECIMAL(2,1))
    comment = Column('comment', Text)
    created = Column('created', DATETIME, default=datetime.now, nullable=False)
    modified = Column('modified', DATETIME, default=datetime.now, nullable=False)
    Index('idx_userid_rstid', user_id, rst_id)
    now = datetime.now()
    def __init__(self, user_id, rst_id, difficulty, comment, created, modified):
        # self.id = id
        self.user_id = user_id
        self.rst_id = rst_id
        self.difficulty = difficulty
        self.comment = comment
        self.created = created
        self.modified = modified

    def __repr__(self):
        return "<UserPost>(user_id:{u_id}, rst_id:{r_id}, difficulty:{diff}"\
                .format(u_id=self.user_id, r_id=self.rst_id, diff=self.difficulty)


class Title(Base):
    __tablename__ = 'title'
    __table_args__ = {'mysql_engine': 'MyISAM'}
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    rank = Column('rank', String(20))
    name = Column('name', Text)
    requirement = Column('requirement', Text)
    stamp = Column('stamp', Text)
    created = Column('created', DATETIME, default=datetime.now, nullable=False)
    modified = Column('modified', DATETIME, default=datetime.now, nullable=False)
    now = datetime.now()
    def __init__(self, name, requirement, stamp, created, modified):
        self.name = name
        self.requirement = requirement
        self.stamp = stamp
        self.created = created
        self.modified = modified

    def __repr__(self):
        return "<Title>(id:{id}, name:{name}, requirement:{requirement})"\
                .format(id=self.id, name=self.name, requirement=self.requirement)

class UserStats(Base):
    __tablename__ = 'user_stats'
    __table_args__ = {'mysql_engine': 'MyISAM'}
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    user_id = Column('user_id', Integer, ForeignKey('user.id'), index=True)
    total = Column('total', Integer, nullable=False, default=0)
    sequence = Column('sequence', Integer, nullable=False, default=0)
    level_1 = Column('level_1', Integer, nullable=False, default=0)
    level_2 = Column('level_2', Integer, nullable=False, default=0)
    level_3 = Column('level_3', Integer, nullable=False, default=0)
    level_4 = Column('level_4', Integer, nullable=False, default=0)
    level_5 = Column('level_5', Integer, nullable=False, default=0)
    sakyo = Column('sakyo', Integer, nullable=False, default=0)
    ukyo = Column('ukyo', Integer, nullable=False, default=0)
    kita = Column('kita', Integer, nullable=False, default=0)
    kamigyo = Column('kamigyo', Integer, nullable=False, default=0)
    shimogyo = Column('shimogyo', Integer, nullable=False, default=0)
    nakagyo = Column('nakagyo', Integer, nullable=False, default=0)
    higashiyama = Column('higashiyama', Integer, nullable=False, default=0)
    yamashina = Column('yamashina', Integer, nullable=False, default=0)
    saikyo = Column('saikyo', Integer, nullable=False, default=0)
    minami = Column('minami', Integer, nullable=False, default=0)
    fushimi = Column('fushimi', Integer, nullable=False, default=0)
    already_acquire = Column('already_acquire', String(255))
    created = Column('created', DATETIME, default=datetime.now, nullable=False)
    modified = Column('modified', DATETIME, default=datetime.now, nullable=False)
    now = datetime.now()
    def __init__(self, user_id, total, sequence, level_1, level_2, level_3,\
            level_4, level_5, sakyo, ukyo, kita, kamigyo, shimogyo, nakagyo,\
            higashiyama, yamashina, saikyo, minami, fushimi, already_acquire,\
            created, modified):
        # self.id = id
        self.user_id = user_id
        self.total = total
        self.sequence = sequence
        self.level_1 = level_1
        self.level_2 = level_2
        self.level_3 = level_3
        self.level_4 = level_4
        self.level_5 = level_5
        self.sakyo = sakyo
        self.ukyo = ukyo
        self.kita = kita
        self.kamigyo = kamigyo
        self.shimogyo = shimogyo
        self.nakagyo = nakagyo
        self.higashiyama = higashiyama
        self.yamashina = yamashina
        self.saikyo = saikyo
        self.minami = minami
        self.fushimi = fushimi
        self.created = created
        self.modified = modified

    def __repr__(self):
        return "<UserStats>(user_id:{u_id}, total:{total}, sequence:{sequence})"\
                .format(u_id=self.user_id, total=self.total, sequence=self.sequence)
