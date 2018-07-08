import datetime

from flask import request
from orator import Schema

from news.lib.db.db import db
from news.models.base import Base

TTL = datetime.timedelta(days=100).total_seconds()


class Ip(Base):
    __table__ = 'ips'
    __fillable__ = ['ip', 'user_id', 'agent']

    @classmethod
    def from_request(cls):
        print(request.headers)
        return cls(ip=request.remote_addr, agent=request.headers.get('User-Agent'))

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists('ips')
        with schema.create('ips') as table:
            table.raw('inet')
            table.integer('user_id').unsigned()
            table.datetime('created_at')

    @classmethod
    def by_user(cls, user):
        return cls.where('user_id', user.id).get()

    @classmethod
    def by_user_id(cls, user_id):
        return cls.where('user_id', user_id).get()

    @classmethod
    def by_ip(cls, ip):
        return cls.where('ip', ip).get()

    @classmethod
    def clean(cls):
        return cls.where()