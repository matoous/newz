from markdown2 import markdown
from orator import Schema
from orator.orm import has_many, morph_many
from redis_lock import Lock
from werkzeug.utils import escape
from wtforms import HiddenField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length

from news.lib.cache import cache
from news.lib.comments import add_new_comment
from news.clients.db.db import db
from news.lib.task_queue import q
from news.lib.utils.confidence import confidence
from news.models.base import Base
from news.models.base_form import BaseForm
from news.models.report import Report


class Comment(Base):
    __table__ = "comments"
    __fillable__ = [
        "id",
        "reported",
        "spam",
        "ups",
        "downs",
        "link_id",
        "parent_id",
        "text",
        "user_id",
    ]
    __hidden__ = ["link", "feed", "user", "votes", "reports"]

    @classmethod
    def create_table(cls):
        """
        Creates database table for comments
        """
        schema = Schema(db)
        schema.drop_if_exists("comments")
        with schema.create("comments") as table:
            table.big_increments("id").unsigned()
            table.big_integer("parent_id").unsigned().nullable()
            table.foreign("parent_id").references("id").on("comments").on_delete(
                "cascade"
            )
            table.text("text")
            table.integer("user_id").unsigned()
            table.foreign("user_id").references("id").on("users")
            table.integer("link_id").unsigned()
            table.foreign("link_id").references("id").on("links").on_delete("cascade")
            table.integer("reported").default(0)
            table.boolean("spam").default(False)
            table.integer("ups").default(0)
            table.integer("downs").default(0)
            table.datetime("created_at")
            table.datetime("updated_at")

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
        return "<Comment {}>".format(self.id)

    @property
    def link(self):
        """
        Get link to which this comments belongs
        :return: Parent Link of Comment
        """
        from news.models.link import Link

        if not "link" in self._relations:
            self._relations["link"] = Link.by_id(self.link_id)
        return self._relations["link"]

    @property
    def user(self):
        """
        Get user who created this link
        :return: Creator of Comment
        """
        from news.models.user import User

        if not "user" in self._relations:
            self._relations["user"] = User.by_id(self.user_id)
        return self._relations["user"]

    @has_many
    def votes(self):
        """
        Get all votes for given comment
        :return: Votes for Comment
        """
        from news.models.vote import CommentVote

        return CommentVote

    def vote_by(self, user):
        """
        Get comment vote by user
        :param user: user
        :return: vote for comment by given user
        """
        from news.models.vote import CommentVote

        if user.is_anonymous:
            return None
        return CommentVote.by_comment_and_user(self.id, user.id)

    @property
    def num_votes(self):
        """
        Number of votes on given comment
        :return: ups + downs
        """
        return self.ups + self.downs

    @morph_many("reportable")
    def reports(self):
        return Report

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
        q.enqueue(add_new_comment, self.link.id, self, result_ttl=0)

    @property
    def route(self):
        return "/c/{}".format(self.id)

    def remove(self):
        """
        Soft remove of the comment from Link
        Changes the text of the comment to <removed>
        """
        # TODO REMOVE FROM CACHE
        self.text = escape("<removed>")
        self.update_with_cache()


class TreeNotBuildException(Exception):
    pass


class CommentTree:
    """
    CommentTree is interface to unordered comment tree for given link
    """

    def __init__(self, link_id):
        self.link_id = link_id
        self._tree = None

    @property
    def _cache_key(self):
        return "ct:{}".format(self.link_id)

    @property
    def _lock_key(self):
        """
        Gets lock key for read/modify/write operations
        :param link: link
        :return: redis key
        """
        return "c_lock:{}".format(self.link_id)

    def create(self):
        cache.set(self._cache_key, {})

    def add(self, comments: ["Comment"]):
        """
        Adds comment to comment tree for given link
        :param link: link
        :param comment: comment
        """
        with Lock(cache.conn, self._lock_key):
            tree = self.load_tree()
            for comment in comments:
                tree.setdefault(comment.parent_id, []).append(comment.id)
            cache.set(self._cache_key, tree)

    def remove(self, comments: ["Comment"]):
        """
        Remove comments from comment tree
        :param comments: comments
        """
        with Lock(cache.conn, self._lock_key):
            tree = self.load_tree()
            for comment in comments:
                tree[comment.parent_id] = [
                    id for id in tree[comment.parent_id] if id != comment.id
                ]
            cache.set(self._cache_key, tree)

    def load_tree(self) -> dict:
        """
        Load the tree
        :return: tree
        """
        tree = cache.get(self._cache_key)
        if not tree:
            comments = (
                Comment.where("link_id", self.link_id).select("parent_id", "id").get()
                or []
            )
            tree = {}
            for comment in comments:
                tree.setdefault(comment.parent_id, []).append(comment.id)
            cache.set(self._cache_key, tree)
        self._tree = tree
        return tree

    def ids(self) -> [str]:
        if not self._tree:
            self.load_tree()
        x = set()
        for parent_id, children_ids in self._tree.items():
            x.add(parent_id)
            for children_id in children_ids:
                x.add(children_id)
        if None in x:
            x.remove(None)
        return list(x)

    @classmethod
    def by_link(cls, link):
        return cls.by_link_id(link.id)

    @property
    def tree(self):
        return self.load_tree()

    def keys(self):
        return self.tree.keys()

    @classmethod
    def by_link_id(cls, link_id):
        """
        Get comment tree by link
        :param link: link
        :return: comment tree
        """
        return CommentTree(link_id)


class SortedComments:
    """
    SortedComments class allows access to sorted comments for links

    Sorted comments are stored in redis
    Key is combination of link id and parent comment id (root comments don't have parent comment id)
    This way all we need to do to update the tree is update comments only under the parent comment
    To get the tree we recursively traverse the tree a fetch children comments
    """

    def __init__(self, link_id):
        self._link_id = link_id
        self._tree = CommentTree.by_link_id(link_id)

    def _cache_key(self, parent_id):
        return "scm:{}.{}".format(self._link_id, parent_id or 0)

    def _lock_key(self, parent_id):
        return "lock:scm:{}.{}".format(self._link_id, parent_id or 0)

    def update(self, comments: ["Comment"]):
        """
        Update sorted comments in cache
        This should be called on votes (maybe not all of them) and on new comments
        :param link_id: link id
        :param comment: comment
        """
        for comment in comments:
            cache_key = self._cache_key(comment.parent_id)
            lock_key = self._lock_key(comment.parent_id)

            # update comment under read - write - modify lock
            with Lock(cache.conn, lock_key):
                # maybe check against the comment tree to see if it is missing or it just is not initialized yet
                comments = (
                    cache.get(cache_key) or []
                )  # so maybe load comments instead of []

                # update comment
                for i in range(len(comments)):
                    if comments[i][0] == comment.id:
                        comments[i] = [
                            comment.id,
                            confidence(comment.ups, comment.downs),
                        ]
                        break
                else:
                    # add comment
                    comments.append(
                        [comment.id, confidence(comment.ups, comment.downs)]
                    )

                # sort and save
                comments = sorted(comments, key=lambda x: x[1:], reverse=True)
                cache.set(cache_key, comments)

    def build_tree(self):
        """
        Build sorted tree of comments for given comment_id
        If comment_id is None, tree for whole link is build
        :param comment_id: comment_id for comment, None for link
        :return: (comment_id, [sorted subtrees])
        """
        # load all comments that will be needed
        comment_ids = self._tree.ids()
        comments = (
            {comment.id: comment for comment in Comment.by_ids(comment_ids)}
            if comment_ids
            else {}
        )
        comments.setdefault(None)

        ids = self._tree.keys()
        children_tuples = cache.mget([self._cache_key(id) for id in ids]) if ids else []
        for idx, parent_id in enumerate(ids):
            # fill in missing children
            if children_tuples[idx] is None:
                children = (
                    Comment.where("parent_id", parent_id)
                    .where("link_id", self._link_id)
                    .get()
                )
                tuples = [[x.id, confidence(x.ups, x.downs)] for x in children]
                children_tuples[idx] = sorted(tuples, key=lambda x: x[1:], reverse=True)
                cache.set(self._cache_key(parent_id), children_tuples[idx])

        builder = dict(zip(ids, children_tuples))

        # subtree builder
        def build_subtree(parent):
            return [
                comments[parent],
                [build_subtree(children_id) for children_id, _ in builder[parent]]
                if parent in builder
                else [],
            ]

        return build_subtree(None)

    def get_full_tree(self):
        """
        Gets full comment tree for given Link
        :return: Sorted Comments tree
        """
        _, tree = self.build_tree()
        return tree


class CommentForm(BaseForm):
    text = TextAreaField("comment", [DataRequired(), Length(max=8192)])
    parent_id = HiddenField(
        "parent_id", [Optional()], render_kw={"class": "parent_comment_id"}
    )

    def result(self):
        return Comment(
            text=markdown(self.text.data, safe_mode="escape"),
            parent_id=int(self.parent_id.data) if self.parent_id.data != "" else None,
        )
