from base64 import urlsafe_b64encode
from os import urandom

from orator import Schema, Model

from news.clients.db.db import db


class DisposableToken(Model):
    __table__ = "tokens"
    __guarded__ = ["value"]
    __timestamps__ = False
    __incrementing__ = False

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists("tokens")
        with schema.create("tokens") as table:
            table.string("id", 40)
            table.primary("id")

    @classmethod
    def _generate_token(cls, size):
        return str(urlsafe_b64encode(urandom(size))[:-1], "utf-8")

    @classmethod
    def get(cls):
        """
        Get secure and disposable token
        :return:
        """
        for i in range(3):
            id = cls._generate_token(20)
            token = DisposableToken.where("id", id).first()
            if token is None:
                return DisposableToken.create({"id": id})
