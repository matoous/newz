from orator.exceptions.query import QueryException
from orator.orm import belongs_to

from news.lib.db.db import db, schema
from news.models.link import Link
from news.models.user import User


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

    def is_downvote(self):
        return self.vote_type == -1

    def is_upvote(self):
        return self.vote_type == 1

    def apply(self):
        vote = Vote.where('user_id', self.user_id).where('link_id',self.link_id).first()
        if vote is None: # new vote
            try:
                with db.transaction():
                    self.save()
                    db.table('links').where('id', self.link_id).increment('score', self.vote_type)
                return True
            except QueryException as e:
                return False
        if vote.vote_type == self.vote_type:
            return True
        if self.is_upvote(): # from downvote to upvote
            try:
                with db.transaction():
                    Vote.where('user_id',self.user_id).where('link_id',self.link_id).update({'vote_type': self.vote_type})
                    db.table('links').where('id', self.link_id).increment('score', 2)
                return True
            except QueryException as e:
                return False
        else: # from upvote to downvote
            try:
                with db.transaction():
                    Vote.where('user_id',self.user_id).where('link_id',self.link_id).update({'vote_type':self.vote_type})
                    db.table('links').where('id', self.link_id).decrement('score', 2)
                return True
            except QueryException as e:
                return False

    def unvote(self):
        vote = Vote.where('user_id', self.user_id).where('link_id',self.link_id).first()
        if vote is None:
            return False
        if vote.is_downvote():
            try:
                with db.transaction():
                    db.table('votes').where('link_id', self.link_id).where('user_id', self.user_id).delete()
                    db.table('links').where('id', self.link_id).increment('score', 1)
                return True
            except QueryException as e:
                return False
        else:
            try:
                with db.transaction():
                    db.table('votes').where('link_id', self.link_id).where('user_id', self.user_id).delete()
                    db.table('links').where('id', self.link_id).decrement('score', 1)
                return True
            except QueryException as e:
                return False