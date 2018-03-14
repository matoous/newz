from enum import IntEnum

from orator import Model
from orator.orm import belongs_to

from news.lib.cache import cache
from news.lib.db.db import db, schema
from news.lib.queue import q
from news.lib.cache_updates import update_link
from news.models.link import Link
from news.models.user import User

UPVOTE = 1
UNVOTE = 0
DOWNVOTE = -1


def vote_type_from_string(str):
    str = str.upper()
    if str == "UPVOTE":
        return 1
    if str == "DOWNVOTE":
        return -1
    return 0


class Vote(Model):
    __table__ = 'votes'
    __fillable__ = ['vote_type', 'user_id', 'link_id']
    __timestamps__ = False
    __incrementing__ = False

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

    @property
    def _id(self):
        return "{}_{}".format(self.user_id, self.link_id)

    @property
    def is_downvote(self):
        return self.vote_type == -1

    @property
    def is_upvote(self):
        return self.vote_type == 1

    @property
    def affected_attribute(self):
        if self.is_downvote:
            return 'downs'
        if self.is_upvote:
            return 'ups'
        return None

    def commit(self):
        self.apply()
        # change users params (more karma/trust factor or something)

    @classmethod
    def by_link_and_user(cls, link_id, user_id):
        cache_key = '{}_{}'.format(link_id, user_id)
        v = cache.get(cache_key)
        if v is not None:
            return v
        v = Vote.where('user_id', user_id).where('link_id', link_id).first()
        cache.set(cache_key, v)
        return v


    def apply(self):
        previous_vote = Vote.where('user_id', self.user_id).where('link_id', self.link_id).first()

        if previous_vote and previous_vote.affected_attribute:
            db.table('links').where('id', self.link_id).decrement(previous_vote.affected_attribute, 1)

        if self.affected_attribute:
            db.table('links').where('id', self.link_id).increment(self.affected_attribute, 1)

        if previous_vote is None:
            self.save()
        else:
            Vote.where('user_id', self.user_id).where('link_id', self.link_id).update({'vote_type': self.vote_type})

        if self.link.num_votes < 20 or self.link.num_votes % 8 == 0:
            q.enqueue(update_link, self.link, result_ttl=0)
