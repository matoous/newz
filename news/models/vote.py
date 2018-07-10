from orator import Model, accessor, Schema
from orator.orm import belongs_to

from news.lib.cache import cache
from news.lib.cache_updates import update_link
from news.lib.comments import update_comment
from news.lib.db.db import db
from news.lib.task_queue import q
from news.models.comment import Comment
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
    __timestamps__ = False
    __incrementing__ = False
    __hidden__ = ['lazy_props']

    @classmethod
    def create_table(cls):
        raise NotImplementedError

    @belongs_to
    def user(self):
        return User

    @belongs_to
    def thing(self):
        raise NotImplementedError

    @classmethod
    def _cache_key(cls, link_id, user_id):
        raise NotImplementedError

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


class LinkVote(Vote):
    __table__ = 'link_votes'
    __fillable__ = ['user_id', 'link_id', 'vote_type']
    __timestamps__ = False
    __incrementing__ = False

    def thing(self):
        return None

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists('link_votes')
        with schema.create('link_votes') as table:
            table.integer('user_id').unsigned()
            table.foreign('user_id').references('id').on('users').on_delete('cascade')
            table.big_integer('link_id').unsigned()
            table.foreign('link_id').references('id').on('links').on_delete('cascade')
            table.integer('vote_type')
            table.primary(['user_id', 'link_id'])

    def __eq__(self, other):
        return self.user_id == other.user_id and self.link_id == other.link_id and self.vote_type == other.vote_type

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "<LinkVote {}:{} {}>".format(self.user_id, self.link_id, self.vote_type)

    @accessor
    def user(self):
        return User.by_id(self.user_id)

    @accessor
    def link(self):
        return Link.by_id(self.link_id)

    @classmethod
    def _cache_key(cls, link_id, user_id):
        return 'lv:{}_{}'.format(link_id, user_id)

    def commit(self):
        self.apply()
        # change users params (more karma/trust factor or something)

    @classmethod
    def by_link_and_user(cls, link_id, user_id):
        cache_key = cls._cache_key(link_id, user_id)
        return cache.get(cache_key)

    def _write_to_cache(self):
        cache_key = self.__class__._cache_key(self.link_id, self.user_id)
        cache.set(cache_key, self, ttl=0)

    def apply(self):
        previous_vote = LinkVote.where('user_id', self.user_id).where('link_id', self.link_id).first()

        if previous_vote and previous_vote.vote_type == self.vote_type:
            return

        if previous_vote and previous_vote.affected_attribute:
            self.link.decr(previous_vote.affected_attribute, 1)

        if self.affected_attribute:
            self.link.incr(self.affected_attribute, 1)

        if previous_vote is None:
            self.save()
        else:
            LinkVote.where('user_id', self.user_id).where('link_id', self.link_id).update({'vote_type': self.vote_type})

        self._write_to_cache()

        if self.link.num_votes < 20 or self.link.num_votes % 8 == 0:
            q.enqueue(update_link, self.link, result_ttl=0)


class CommentVote(Vote):
    __table__ = 'comment_votes'
    __fillable__ = ['user_id', 'comment_id', 'vote_type']
    __timestamps__ = False
    __incrementing__ = False

    def thing(self):
        return None

    def __repr__(self):
        return "<CommentVote {}:{} {}>".format(self.user_id, self.comment_id, self.vote_type)

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists('comment_votes')
        with schema.create('comment_votes') as table:
            table.integer('user_id').unsigned()
            table.foreign('user_id').references('id').on('users').on_delete('cascade')
            table.big_integer('comment_id').unsigned()
            table.foreign('comment_id').references('id').on('comments').on_delete('cascade')
            table.integer('vote_type')
            table.primary(['user_id', 'comment_id'])

    @accessor
    def user(self):
        return User.by_id(self.user_id)

    @accessor
    def comment(self):
        return Comment.by_id(self.comment_id)

    @classmethod
    def _cache_key(cls, comment_id, user_id):
        return 'cv:{}_{}'.format(comment_id, user_id)

    def commit(self):
        self.apply()
        # change users params (more karma/trust factor or something)

    @classmethod
    def by_comment_and_user(cls, comment_id, user_id):
        cache_key = cls._cache_key(comment_id, user_id)
        return cache.get(cache_key)

    def _write_to_cache(self):
        cache_key = self.__class__._cache_key(self.comment_id, self.user_id)
        cache.set(cache_key, self, ttl=0)

    def apply(self):
        previous_vote = CommentVote.where('user_id', self.user_id).where('comment_id', self.comment_id).first()
        if previous_vote and previous_vote.vote_type == self.vote_type:
            return

        if previous_vote and previous_vote.affected_attribute:
            self.comment.decr(previous_vote.affected_attribute, 1)

        if self.affected_attribute:
            self.comment.incr(self.affected_attribute, 1)

        if previous_vote is None:
            self.save()
        else:
            CommentVote.where('user_id', self.user_id).where('comment_id', self.comment_id).update({'vote_type': self.vote_type})

        self._write_to_cache()

        if self.comment.num_votes < 20 or self.comment.num_votes % 8 == 0:
            q.enqueue(update_comment, self.comment, result_ttl=0)

