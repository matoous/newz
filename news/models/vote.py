from orator import Model
from orator.orm import belongs_to

from news.lib.cache import cache
from news.lib.comments import update_comment
from news.lib.db.db import db, schema
from news.lib.queue import q
from news.lib.cache_updates import update_link
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


class LinkVote(Vote, Model):
    __table__ = 'link_votes'
    __fillable__ = ['user_id', 'link_id', 'vote_type']
    __timestamps__ = False
    __incrementing__ = False

    def thing(self):
        return None

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('link_votes')
        with schema.create('link_votes') as table:
            table.integer('user_id').unsigned()
            table.foreign('user_id').references('id').on('users').on_delete('cascade')
            table.big_integer('link_id').unsigned()
            table.foreign('link_id').references('id').on('links')
            table.integer('vote_type')
            table.primary(['user_id', 'link_id'])

    @property
    def user(self):
        return User.by_id(self.user_id)

    @property
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
        v = cache.get(cache_key)
        if v is not None:
            return v
        v = cls.where('user_id', user_id).where('link_id', link_id).first()
        cache.set(cache_key, v)
        return v

    def apply(self):
        previous_vote = LinkVote.where('user_id', self.user_id).where('link_id', self.link_id).first()
        if previous_vote and previous_vote.vote_type == self.vote_type:
            return

        if previous_vote and previous_vote.affected_attribute:
            Link.where('id', self.link_id).decrement(previous_vote.affected_attribute, 1)

        if self.affected_attribute:
            Link.where('id', self.link_id).increment(self.affected_attribute, 1)

        if previous_vote is None:
            self.save()
        else:
            LinkVote.where('user_id', self.user_id).where('link_id', self.link_id).update({'vote_type': self.vote_type})

        cache_key = LinkVote._cache_key(self.link_id, self.user_id)
        cache.set(cache_key, self)
        if self.link.num_votes < 20 or self.link.num_votes % 8 == 0:
            q.enqueue(update_link, self.link, result_ttl=0)


class CommentVote(Vote, Model):
    __table__ = 'comment_votes'
    __fillable__ = ['user_id', 'comment_id', 'vote_type']
    __timestamps__ = False
    __incrementing__ = False

    def thing(self):
        return None

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('comment_votes')
        with schema.create('comment_votes') as table:
            table.integer('user_id').unsigned()
            table.foreign('user_id').references('id').on('users').on_delete('cascade')
            table.big_integer('comment_id').unsigned()
            table.foreign('comment_id').references('id').on('comments')
            table.integer('vote_type')
            table.primary(['user_id', 'comment_id'])

    @property
    def user(self):
        return User.by_id(self.user_id)

    @property
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
        v = cache.get(cache_key)
        if v is not None:
            return v
        v = cls.where('user_id', user_id).where('comment_id', comment_id).first()
        cache.set(cache_key, v)
        return v

    def apply(self):
        previous_vote = CommentVote.where('user_id', self.user_id).where('comment_id', self.comment_id).first()
        if previous_vote and previous_vote.vote_type == self.vote_type:
            return

        if previous_vote and previous_vote.affected_attribute:
            Comment.where('id', self.comment_id).decrement(previous_vote.affected_attribute, 1)

        if self.affected_attribute:
            Comment.where('id', self.comment_id).increment(self.affected_attribute, 1)

        if previous_vote is None:
            self.save()
        else:
            CommentVote.where('user_id', self.user_id).where('comment_id', self.comment_id).update({'vote_type': self.vote_type})

        cache_key = CommentVote._cache_key(self.comment_id, self.user_id)
        cache.set(cache_key, self)
        Comment.update_cache(self.comment)
        if self.comment.num_votes < 20 or self.comment.num_votes % 8 == 0:
            q.enqueue(update_comment, self.comment, result_ttl=0)
