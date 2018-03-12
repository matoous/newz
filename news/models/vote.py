from enum import IntEnum

from orator.orm import belongs_to

from news.lib.db.db import db, schema
from news.models.link import Link
from news.models.user import User


class VoteType(IntEnum):
    UPVOTE = 1
    UNVOTE = 0
    DOWNVOTE = -1

    @classmethod
    def from_string(cls, str):
        str = str.upper()
        if str == 'UPVOTE':
            return VoteType.UPVOTE
        if str == "DOWNVOTE":
            return VoteType.DOWNVOTE
        if str == "UNVOTE":
            return VoteType.UNVOTE
        return None


class Vote(db.Model):
    __table__ = 'votes'
    __fillable__ = ['vote_type', 'user_id', 'link_id']
    __timestamps__ = False

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

    @property
    def _id(self):
        return "{}_{}".format(self.user_id, self.link_id)

    def is_downvote(self):
        return self.vote_type == VoteType.DOWNVOTE

    def is_upvote(self):
        return self.vote_type == VoteType.UPVOTE

    def affected_attribute(self):
        if self.is_downvote():
            return 'downs'
        if self.is_upvote():
            return 'ups'
        return None

    def commit(self):
        self.apply()
        # update thing in cache if self.thing.num_votes < 20 or self.thing.num_votes % 8 == 0:
        # that's what reddit does

    def apply(self):
        previous_vote = Vote.where('user_id', self.user_id).where('link_id',self.link_id).first()

        if previous_vote and previous_vote.affected_attribute():
            db.table('links').where('id', self.link_id).decrement(previous_vote.affected_attribute(), 1)

        if self.affected_attribute():
            db.table('links').where('id', self.link_id).increment(self.affected_attribute(), 1)

        if previous_vote is None:
            self.save()
        else:
            Vote.where('user_id', self.user_id).where('link_id', self.link_id).update({'vote_type': self.vote_type})