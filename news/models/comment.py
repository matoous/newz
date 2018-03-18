import redis_lock
from flask_wtf import Form
from orator import Model
from orator.orm import has_many, morph_many
from wtforms import StringField, HiddenField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import TextArea

from news.lib.adding import add_to_queries
from news.lib.cache import cache, conn
from news.lib.comments import add_new_comment
from news.lib.db.db import db, schema
from news.lib.queue import q
from news.lib.utils.confidence import confidence
from news.lib.utils.time_utils import time_ago
from news.models.report import Report


class Comment(Model):
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
        q.enqueue(add_new_comment, self.link, self, result_ttl=0)

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
            print(tree)
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
    @classmethod
    def _cache_key(cls, link, parent_id):
        return 'scm:{}.{}'.format(link.id, parent_id) if parent_id else 'scm:{}'.format(link.id)

    @classmethod
    def _lock_key(cls, link, parent_id):
        return 'scm_lock:{}.{}'.format(link.id, parent_id) if parent_id else 'scm_lock:{}'.format(link.id)

    @classmethod
    def update(cls, link, comment):
        cache_key = cls._cache_key(link, comment.parent_id)

        with redis_lock.Lock(conn, cls._lock_key(link, comment.parent_id)):
            comments = cache.get(cache_key) or []
            added = False
            for i in range(len(comments)):
                if comments[i][0] == comment.id:
                    comments[i][1] = confidence(comment.ups, comment.downs)
                    added = True
                    break
            if not added:
                comments.append((comment.id, confidence(comment.ups, comment.downs)))
            comments = sorted(comments, key=lambda x: x[1], reverse=True)
            cache.set(cache_key, comments)

    @classmethod
    def build_tree(cls, link, comment_id=None, depth=-1):
        children_ids = cache.get(cls._cache_key(link, comment_id))
        if children_ids is None or depth == 0:
            return comment_id, []
        else:
            return comment_id, [cls.build_tree(link, children_id, depth - 1) for children_id, _ in children_ids]

    @classmethod
    def get_full_tree(cls, link, limit_main_comments=None, limit_count=None, limit_depth=None):
        tree = cls.build_tree(link)
        return tree[1]


class CommentForm(Form):
    text = StringField('comment', [DataRequired(), TextArea()])
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
