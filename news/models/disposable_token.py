from base64 import urlsafe_b64encode
from os import urandom

from orator import Schema, Model

from news.lib.db.db import db


def generate_token(size):
    return str(urlsafe_b64encode(urandom(size))[:-1], 'utf-8')


class DisposableToken(Model):
    __table__ = 'tokens'
    __guarded__ = ['value']
    __timestamps__ = False  # maybe keep timestemps so we can delete really old tokens a reuse them
    __incrementing__ = False

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists('tokens')
        with schema.create('tokens') as table:
            table.string('id', 40)
            table.primary('id')

    @classmethod
    def get(cls):
        for i in range(3):
            id = generate_token(20)
            token = DisposableToken.where('id', id).first()
            if token is None:
                return DisposableToken.create({'id': id})
