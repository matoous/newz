import redis_lock
from orator import Model
from orator.orm import has_many, morph_many
from news.lib.adding import add_to_queries
from news.lib.cache import cache, conn
from news.lib.db.db import db, schema
from news.lib.queue import q
from news.lib.utils.time_utils import time_ago
from news.models.report import Report


class Comment(Model):
    __table__ = 'comments'
    __fillable__ = ['link_id', 'parent_id', 'text', 'user_id']
    __guarded__ = ['id', 'reported', 'spam', 'ups', 'downs']
    __hidden__ = ['reported', 'spam']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('links')
        with schema.create('links') as table:
            table.big_integer('id').unsigned()
            table.big_integer('parent_id').unsigned().nullable()
            table.text('text')
            table.integer('user_id').unsigned()
            table.integer('link_id').unsigned()
            table.integer('reported').default(0)
            table.boolean('spam').default(False)
            table.integer('ups').default(0)
            table.integer('downs').default(0)

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

    @classmethod
    def _cache_prefix(cls):
        return "c:"

    def time_ago(self):
        return time_ago(self.created_at)

    @property
    def score(self):
        return self.ups - self.downs

    def commit(self):
        self.save()
        self.ups = self.downs = 0

        #self.link.incr(comments_count)
        #q.enqueue(add_to_tree, self, result_ttl=0) -> add to tree, add to comment sorting

    @classmethod
    def _cache_key(cls, id):
        return 'cm:{}'.format(id)

    @classmethod
    def by_id(cls, id):
        cache_key = cls._cache_key(id)
        comment = cache.get(cache_key)
        if comment is None:
            comment = cls.where('id', id).first()
            cache.set(cache_key, comment)
        return comment


class CommentTreeCache:
    def __init__(self, link_id, tree):
        self.link_id = link_id
        self.tree = tree

    @classmethod
    def _cache_key(cls, link):
        return 'ct:{}'.format(link.id)

    @classmethod
    def _write_tree(cls, link, tree, lock):
        key = cls._cache_key(link)
        cache.set(key, tree)

    @classmethod
    def _lock_key(cls, link):
        return 'c_lock:{}'.format(link.id)

    @classmethod
    def rebuild(cls, link, comments):
        with redis_lock.Lock(conn, cls._lock_key(link)) as lock:
            tree = {}
            for comment in comments:
                tree.setdefault(comment.parent_id, []).append(comment.id)

            cls._write_tree(link, tree, lock)
            return cls(link.id, tree)

    @classmethod
    def load_tree(cls, link):
        tree = cache.get(cls._cache_key(link))
        return tree or {}


class CommentTree:
    def __init__(self, link, tree):
        self.link = link
        self.tree = tree

    @classmethod
    def by_link(cls, link):
        tree = CommentTreeCache.load_tree(link)
        if tree == {}:
            tree = cls._rebuild(link)
        return cls(link, tree)

    @classmethod
    def _rebuild(cls, link):
        comments = Comment.where('link_id', link.id).get()
        res = CommentTreeCache.rebuild(link, comments)
        return res.tree


class SortedComments:
    @classmethod
    def update(cls, parent_id, comment_id):
        pass

    @classmethod
    def get_by_id(cls, comment_id):
        pass

    @classmethod
    def get_full_tree(cls, link, limit_main_comments=None, limit_count=None, limit_depth=None):
        #  build full sorted tree of comment_ids
        pass
