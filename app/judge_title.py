# -*- encoding:utf-8 -*-

from Table import Session, Tabelog, UserPost, UserStats
from sqlalchemy import func
import re
import datetime

class JudgeTitle(object):
    def __init__(self, user_id):
        self.user_id = user_id
