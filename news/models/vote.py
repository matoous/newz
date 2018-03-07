from orator.orm import belongs_to

from news.lib.db.db import db, schema
from news.models.link import Link
from news.models.user import User


class Vote(db.Model):
    __table__ = 'votes'
    __fillable__ = ['vote_type','user_id','link_id']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('votes')
        with schema.create('votes') as table:
            table.big_integer('user_id')
            table.foreign('user_id').references('id').on('users').on_delete('cascade')
            table.big_integer('link_id')
            table.foreign('link_id').references('id').on('links')
            table.integer('vote_type')
            table.primary(['user_id', 'link_id'])

    @belongs_to
    def user(self):
        return User

    @belongs_to
    def link(self):
        return Link

    @classmethod
    def _cache_prefix(cls):
        return "v:"