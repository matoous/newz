from flask_wtf import Form
from redis_lock import Lock
from orator.orm import has_many, morph_many
from wtforms import HiddenField, TextAreaField
from wtforms.validators import DataRequired, Optional

from news.lib.cache import cache, conn
from news.lib.comments import add_new_comment
from news.lib.db.db import schema
from news.lib.lazy import lazyprop
from news.lib.queue import q
from news.lib.utils.confidence import confidence
from news.lib.utils.time_utils import time_ago
from news.models.base import Base
from news.models.report import Report


class Comment(Base):
    __table__ = 'comments'
    __fillable__ = ['id', 'reported', 'spam', 'ups', 'downs', 'link_id', 'parent_id', 'text', 'user_id']

    @classmethod
    def create_table(cls):
        """
        Creates database table for comments
        """
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
        """
        Override default cache prefix with shorter one
        :return: c:
        """
        return "c:"

    def __eq__(self, other):
        if not isinstance(other, Comment):
            return False
        return other.id == self.id

    def __repr__(self):
        return '<Comment {}>'.format(self.id)

    @lazyprop
    def link(self):
        """
        Get link to which this comments belongs
        :return: Parent Link of Comment
        """
        from news.models.link import Link
        return Link.by_id(self.link_id)

    @lazyprop
    def user(self):
        """
        Get user who created this link
        :return: Creator of Comment
        """
        from news.models.user import User
        return User.by_id(self.user_id)

    @has_many
    def votes(self):
        """
        Get all votes for given comment
        :return: Votes for Comment
        """
        from news.models.vote import CommentVote
        return CommentVote

    @property
    def num_votes(self):
        """
        Number of votes on given comment
        :return: ups + downs
        """
        return self.ups + self.downs

    @morph_many('reportable')
    def reports(self):
        return Report

    def time_ago(self):
        return time_ago(self.created_at)

    @property
    def score(self):
        """
        Current score of comment as ups - downs
        No modifications are done to the result
        :return: ups - downs
        """
        return self.ups - self.downs

    def commit(self):
        """
        Creates new comment and handles all tasks resulting from this action
        """
        self.save()
        self.ups = self.downs = 0
        q.enqueue(add_new_comment, self.link, self, result_ttl=0)

    @classmethod
    def by_id(cls, id):
        """
        Gets comment by id from cache
        Writes comment to cache on cache miss
        :param id: comment id
        :return: comment
        """
        c = cls.load_from_cache(id)
        if c is not None:
            return c
        c = cls.where('id', id).first()
        c.write_to_cache()
        conn.expire(c._cache_key, 7 * 24 * 60 * 60)  # expire after week
        return c


class TreeNotBuildException(Exception):
    pass


class CommentTreeCache:
    """
    Caching class for comment tree for link
    """
    def __init__(self, link_id, tree):
        self.link_id = link_id
        self.tree = tree

    @classmethod
    def _cache_key(cls, link):
        return 'ct:{}'.format(link.id)

    @classmethod
    def _write_tree(cls, link, tree):
        """
        Writes tree to redis
        :param link: link
        :param tree: tree
        """
        key = cls._cache_key(link)
        cache.set(key, tree)

    @classmethod
    def _lock_key(cls, link):
        """
        Gets lock key for read/modify/write operations
        :param link: link
        :return: redis key
        """
        return 'c_lock:{}'.format(link.id)

    @classmethod
    def add(cls, link, comment):
        """
        Adds comment to comment tree for given link
        :param link: link
        :param comment: comment
        """
        with Lock(conn, cls._lock_key(link)):
            tree = cls.load_tree(link)
            if not tree:
                raise TreeNotBuildException
            tree.setdefault(comment.parent_id, []).append(comment.id)
            cache.set(cls._cache_key(link), tree)

    @classmethod
    def rebuild(cls, link, comments):
        """
        Rebuilds comment tree for link from passed comments
        :param link: link
        :param comments: comments
        :return:
        """
        with Lock(conn, cls._lock_key(link)): # todo lock in CommentTree not here, so we dont fetch all comments more times on miss
            tree = {}
            for comment in comments:
                tree.setdefault(comment.parent_id, []).append(comment.id)

            cls._write_tree(link, tree)  # save tree to redis
            return cls(link.id, tree)

    @classmethod
    def load_tree(cls, link):
        tree = cache.get(cls._cache_key(link))
        return tree


class CommentTree:
    """
    CommentTree is interface to unordered comment tree for given link

    CommentTree uses CommentTreeCache od background to access and modify comments for given link
    """
    def __init__(self, link, tree):
        self.link = link
        self.tree = tree

    @classmethod
    def add(cls, link, comment):
        """
        Adds comment to comment tree
        :param link: link
        :param comment: comment to insert
        """
        try:
            CommentTreeCache.add(link, comment)
        except TreeNotBuildException:
            CommentTree._rebuild(link)

    @classmethod
    def by_link(cls, link):
        """
        Get comment tree by link
        :param link: link
        :return: comment tree
        """
        tree = CommentTreeCache.load_tree(link)
        if tree is None:
            tree = cls._rebuild(link)
        return cls(link, tree)

    @classmethod
    def _rebuild(cls, link):
        """
        Rebuild the comment tree from database
        :param link: link
        :return: comment tree
        """
        comments = Comment.where('link_id', link.id).select('parent_id', 'id').get() or []
        res = CommentTreeCache.rebuild(link, comments)
        return res.tree


class SortedComments:
    """
    SortedComments class allows access to sorted comments for links

    Sorted comments are stored in redis
    Key is combination of link id and parent comment id (root comments don't have parent comment id)
    This way all we need to do to update the tree is update comments only under the parent comment
    To get the tree we recursively traverse the tree a fetch children comments
    """
    def __init__(self, link):
        self.link = link
        self._tree = CommentTree.by_link(link).tree

    @classmethod
    def _cache_key(cls, link, parent_id):
        return 'scm:{}.{}'.format(link.id, parent_id) if parent_id else 'scm:{}'.format(link.id)

    @classmethod
    def _lock_key(cls, link, parent_id):
        return 'lock:scm:{}.{}'.format(link.id, parent_id) if parent_id else 'lock:scm:{}'.format(link.id)

    @classmethod
    def update(cls, link, comment):
        """
        Update sorted comments in cache
        This should be called on votes (maybe not all of them) and on new comments
        :param link: link
        :param comment: comment
        """
        cache_key = cls._cache_key(link, comment.parent_id)
        # update comment under read - write - modify lock
        with Lock(conn, cls._lock_key(link, comment.parent_id)):
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
        """
        Build sorted tree of comments for given comment_id
        If comment_id is None, tree for whole link is build
        :param comment_id: comment_id for comment, None for link
        :return: (comment_id, [sorted subtrees])
        """
        # get from cache
        children_tuples = cache.get(self._cache_key(self.link, comment_id))

        # cache miss, update
        if children_tuples is None:
            children = Comment.where('parent_id', comment_id).where('link_id', self.link.id).get()
            children_tuples = [(x.id, confidence(x.ups, x.downs)) for x in children]
            cache.set(self._cache_key(self.link, comment_id), children_tuples)

        return comment_id, [self.build_tree(children_id) for children_id, _ in children_tuples]

    def get_full_tree(self):
        """
        Gets full comment tree for given Link
        :return: Sorted Comments tree
        """
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
