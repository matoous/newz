import redis_lock
from flask_wtf import Form
from orator import Model
from orator.orm import has_many, morph_many
from wtforms import HiddenField, TextAreaField
from wtforms.validators import DataRequired, Optional

from news.lib.cache import cache, conn
from news.lib.comments import add_new_comment
from news.lib.db.db import schema
from news.lib.queue import q
from news.lib.utils.confidence import confidence
from news.lib.utils.time_utils import time_ago
from news.models.base import Base
from news.models.report import Report


class Comment(Base):
    __table__ = 'comments'
    __fillable__ = ['link_id', 'parent_id', 'text', 'user_id']
    __guarded__ = ['id', 'reported', 'spam', 'ups', 'downs']
    __hidden__ = ['reported', 'spam']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('comments')
        with schema.create('comments') as table:
            table.big_increments('id').unsigned()
            table.big_integer('parent_id').unsigned().nullable()
            table.text('text')
            table.integer('user_id').unsigned()
            table.integer('link_id').unsigned()
            table.integer('reported').default(0)
            table.boolean('spam').default(False)
            table.integer('ups').default(0)
            table.integer('downs').default(0)
            table.datetime('created_at')
            table.datetime('updated_at')

    @classmethod
    def _cache_prefix(cls):
        return "c:"

    def __eq__(self, other):
        if not isinstance(other, Comment):
            return False
        return other.id == self.id

    def __repr__(self):
        return '<Comment {}>'.format(self.id)

    @property
    def link(self):
        from news.models.link import Link
        return Link.by_id(self.link_id)

    @property
    def user(self):
        from news.models.user import User
        return User.by_id(self.user_id)

    @has_many
    def votes(self):
        from news.models.vote import Vote
        return Vote

    @property
    def num_votes(self):
        return self.ups + self.downs

    @morph_many('reportable')
    def reports(self):
        return Report

    def time_ago(self):
        return time_ago(self.created_at)

    @property
    def score(self):
        return self.ups - self.downs

    def commit(self):
        self.save()
        self.ups = self.downs = 0
        q.enqueue(add_new_comment, self.link, self, result_ttl=0)

    @classmethod
    def by_id(cls, id):
        cache_key = cls._cache_key_from_id(id)
        comment = cache.get(cache_key)
        if comment is None:
            comment = cls.where('id', id).first()
            cache.set(cache_key, comment)
            conn.expire(cache_key, 7 * 24 * 60 * 60) # expire after week
        return comment


class TreeNotBuildException(Exception):
    pass


class CommentTreeCache:
    def __init__(self, link_id, tree):
        self.link_id = link_id
        self.tree = tree

    @classmethod
    def _cache_key(cls, link):
        return 'ct:{}'.format(link.id)

    @classmethod
    def _write_tree(cls, link, tree):
        key = cls._cache_key(link)
        cache.set(key, tree)

    @classmethod
    def _lock_key(cls, link):
        return 'c_lock:{}'.format(link.id)

    @classmethod
    def add(cls, link, comment):
        with redis_lock.Lock(conn, cls._lock_key(link)):
            tree = cls.load_tree(link)
            if not tree:
                raise TreeNotBuildException
            tree.setdefault(comment.parent_id, []).append(comment.id)
            cache.set(cls._cache_key(link), tree)

    @classmethod
    def rebuild(cls, link, comments):
        with redis_lock.Lock(conn, cls._lock_key(link)):
            tree = {}
            for comment in comments:
                tree.setdefault(comment.parent_id, []).append(comment.id)

            cls._write_tree(link, tree)
            return cls(link.id, tree)

    @classmethod
    def load_tree(cls, link):
        tree = cache.get(cls._cache_key(link))
        return tree


class CommentTree:
    def __init__(self, link, tree):
        self.link = link
        self.tree = tree

    @classmethod
    def add(cls, link, comment):
        try:
            CommentTreeCache.add(link, comment)
        except TreeNotBuildException:
            CommentTree._rebuild(link)

    @classmethod
    def by_link(cls, link):
        tree = CommentTreeCache.load_tree(link)
        if tree is None:
            tree = cls._rebuild(link)
        return cls(link, tree)

    @classmethod
    def _rebuild(cls, link):
        comments = Comment.where('link_id', link.id).select('parent_id', 'id').get() or []
        res = CommentTreeCache.rebuild(link, comments)
        return res.tree


class SortedComments:
    def __init__(self, link):
        self.link = link
        self._tree = CommentTree.by_link(link).tree

    def _cache_key(self, parent_id):
        return 'scm:{}.{}'.format(self.link.id, parent_id) if parent_id else 'scm:{}'.format(self.link.id)

    @classmethod
    def _lock_key(cls, link, parent_id):
        return 'lock:scm:{}.{}'.format(link.id, parent_id) if parent_id else 'lock:scm:{}'.format(link.id)

    @classmethod
    def update(cls, link, comment):
        cache_key = cls._cache_key(link, comment.parent_id)
        # update comment under read - write - modify lock
        with redis_lock.Lock(conn, cls._lock_key(link, comment.parent_id)):
            comments = cache.get(cache_key) or []
            added = False

            # update comment
            for i in range(len(comments)):
                if comments[i][0] == comment.id:
                    comments[i] = (comment.id, confidence(comment.ups, comment.downs))
                    added = True
                    break

            # add comment
            if not added:
                comments.append((comment.id, confidence(comment.ups, comment.downs)))

            # sort and save
            comments = sorted(comments, key=lambda x: x[1:], reverse=True)
            cache.set(cache_key, comments)

    def build_tree(self, comment_id=None):
        # get from cache
        children_tuples = cache.get(self._cache_key(comment_id))

        # cache miss, update
        if children_tuples is None:
            children = Comment.where('parent_id', comment_id).where('link_id', self.link.id).get()
            children_tuples = [(x.id, confidence(x.ups, x.downs)) for x in children]
            cache.set(self._cache_key(comment_id), children_tuples)

        return comment_id, [self.build_tree(children_id) for children_id, _ in children_tuples]

    def get_full_tree(self):
        tree = self.build_tree()
        return tree[1]


class CommentForm(Form):
    text = TextAreaField('comment', [DataRequired()])
    parent_id = HiddenField('parent_id', [Optional()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.comment = None

    def validate(self, user, link):
        # todo add validation
        self.comment = Comment(text=self.text.data,
                               parent_id=int(self.parent_id.data) if self.parent_id.data != '' else None,
                               user_id=user.id,
                               link_id=link.id)
        return True
