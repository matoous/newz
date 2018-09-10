from typing import Optional

from flask_wtf import FlaskForm
from orator import Model, accessor, Schema
from orator.exceptions.query import QueryException
from orator.orm import morph_many
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, URL

from news.lib.cache import cache
from news.lib.db.db import db
from news.lib.db.query import add_to_queries
from news.lib.db.sorts import sorts
from news.lib.sorts import hot
from news.lib.task_queue import q
from news.lib.utils.slugify import make_slug
from news.models.base import Base
from news.models.comment import Comment
from news.models.report import Report
from news.models.vote import CommentVote, LinkVote

MAX_IN_CACHE = 1000


class Link(Base):
    __table__ = 'links'
    __fillable__ = ['title', 'slug', 'text', 'user_id', 'url', 'feed_id', 'id', 'image',
                    'reported', 'spam', 'archived', 'ups', 'downs', 'comments_count']
    __searchable__ = ['id', 'title', 'text', 'url', 'user_id', 'feed_id', 'created_at', 'ups', 'downs']
    __hidden__ = ['user', 'feed']

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists('links')
        with schema.create('links') as table:
            table.big_increments('id').unsigned()
            table.string('title', 128)
            table.string('slug', 150)
            table.text('text').nullable()
            table.text('image').nullable()
            table.text('url')
            table.integer('user_id').unsigned()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.foreign('user_id').references('id').on('users')
            table.integer('feed_id').unsigned()
            table.foreign('feed_id').references('id').on('feeds').ondelete('cascade')
            table.integer('ups').default(0)
            table.integer('downs').default(0)
            table.integer('comments_count').default(0)
            table.boolean('archived').default(False)
            table.integer('reported').default(0)
            table.boolean('spam').default(False)

    def __init__(self, **attributes):
        super().__init__(**attributes)
        self.ups = self.downs = 0

    @classmethod
    def _cache_prefix(cls):
        return "l:"

    def __eq__(self, other):
        if not isinstance(other, Link):
            return False
        return other.id == self.id

    def __repr__(self):
        return '<Link {}>'.format(self.id)

    @accessor
    def hot(self) -> float:
        """
        Hot score of the link
        :return: hot score
        """
        return hot(self.score, self.created_at)

    @property
    def feed(self) -> 'Feed':
        """
        Feed where the lin was posted
        :return: feed
        """
        from news.models.feed import Feed
        if 'feed' not in self._relations:
            self._relations['feed'] = Feed.by_id(self.feed_id)
        return self._relations['feed']

    @classmethod
    def by_slug(cls, slug) -> Optional['Link']:
        """
        Get link by slug
        :param slug: slug
        :return: maybe link
        """
        cache_key = "lslug:{}".format(slug)
        id = cache.get(cache_key)
        if id is None:
            link = Link.where('slug', slug).first()
            if link is not None:
                id = link.id
                cache.set(cache_key, id)

        return Link.by_id(id) if id else None

    @property
    def user(self) -> 'User':
        """
        Get user who posted the link
        :return:
        """
        from news.models.user import User
        if 'user' not in self._relations:
            self._relations['user'] = User.by_id(self.user_id)
        return self._relations['user']

    @property
    def trimmed_summary(self):
        """
        Get link summary trimmed to 300 chars max for displaying on feeds
        :return:
        """
        return self.text[:max(300, len(self.text))] if self.text else ''

    @accessor
    def votes(self):
        """
        Get link votes
        :return:
        """
        from news.models.vote import LinkVote
        return LinkVote.where('link_id', self.id).get()

    def vote_by(self, user: 'User') -> Optional['LinkVote']:
        """
        Get link vote by user
        :param user: user
        :return: vote
        """
        from news.models.vote import LinkVote
        if user.is_anonymous:
            return None
        return LinkVote.by_link_and_user(self.id, user.id)

    def report(self, report):
        self.reports().save(report)
        self.incr('reported', 1)

    @property
    def num_votes(self) -> int:
        """
        Get the number of votes on this link
        :return:
        """
        return self.ups + self.downs

    @morph_many('reportable')
    def reports(self):
        return Report

    @classmethod
    def by_feed(cls, feed: 'Feed', sort: str) -> ['Link']:
        """
        Get links by feed and sort
        :param feed: feed
        :param sort: sort
        :return: links
        """
        return Link.get_by_feed_id(feed.id, sort)

    @classmethod
    def get_by_feed_id(cls, feed_id: int, sort: str) -> ['Link']:
        """
        Get links by feed id and sort
        :param feed_id:
        :param sort:
        :return:
        """
        cache_key = 'fs:{}.{}'.format(feed_id, sort)

        r = cache.get(cache_key)
        if r is not None:
            return r

        q = Link.where('feed_id', feed_id).order_by_raw(sorts[sort])

        # cache needs array of objects, not a orator collection
        res = [f for f in q.limit(1000).get()]
        # TODO this is stupid, cache only ids?
        cache.set(cache_key, res)
        return res

    @property
    def score(self) -> int:
        """
        Return links score
        :return: score
        """
        return self.ups - self.downs

    def commit(self):
        self.save()
        q.enqueue(add_to_queries, self, result_ttl=0)

    @property
    def full_route(self) -> str:
        """
        Full route of the link

        Full route adds link slug at the end of the url for better readability by humans
        :return: link route
        """
        return "/l/{}/{}".format(self.id, self.slug)

    @property
    def route(self) -> str:
        return "/l/{}".format(self.id)

    def archive(self):
        """
        Archive the link

        Link get archived to save some memory in redis/db by disallowing voting and commenting on old links
        Upon archiving of the link all votes get deleted and only the final score is kept
        Same thing happens with the votes on comments of this link - votes get deleted and only final score is kept
        """

        # delete link votes from DB
        LinkVote.where('link_id', self.id).delete()
        # delete cached link votes
        link_upvotes_key, link_downvotes_key = LinkVote.set_keys(self.id)
        cache.delete(link_upvotes_key)
        cache.delete(link_downvotes_key)

        # delete comment votes
        for comment in Comment.where('link_id', self.id):
            # delete cached comment votes
            comment_upvotes_key, comment_downvotes_key = CommentVote.set_keys(comment.id)
            cache.delete(comment_upvotes_key)
            cache.delete(comment_downvotes_key)
            # delete comment votes from DB
            CommentVote.where('comment_id', comment.id).delete()

        # update self
        with self.get_read_modify_write_lock():
            self.archived = True
            self.update_with_cache()

    @property
    def is_autoposted(self) -> bool:
        """
        Is the link autoposted, e.g. is it from fully qualified source?
        :return:
        """
        return self.user_id == 12345

    @classmethod
    def search(cls, q):
        """
        Search for link by query

        Searches for link by given query
        Uses full text search ability of postgreSQL, currently allows only searching by phrase/words
        no logic is implemented
        :param q: search query
        :return: links
        """
        q = " & ".join(q.split())
        return cls.select_raw(
            'ts_headline(\'english\', "title", plainto_tsquery(\'"{}"\')) AS title_highlight, '
            'ts_headline(\'english\', "text", plainto_tsquery(\'"{}"\')) AS text_highlight, '
            'id, title, text, feed_id, user_id, ups, downs, created_at'.format(q, q)
        ).where_raw(
            'textsearchable_title @@ to_tsquery(\'"{}"\') '
            'OR textsearchable_text @@ to_tsquery(\'"{}"\')'.format(q, q)
        ).order_by_raw('ups - downs DESC').get()


class LinkForm(FlaskForm):
    title = StringField('Title', [DataRequired(), Length(max=128, min=6)],
                        render_kw={'placeholder': 'Title', 'autocomplete': 'off'})
    url = StringField('Url', [DataRequired(), URL(), Length(max=256)],
                      render_kw={'placeholder': 'URL', 'oninput': 'handleUrlChange()', 'autocomplete': 'off'})
    text = TextAreaField('Summary', [Length(max=8192)],
                         render_kw={'placeholder': 'Summary or text', 'rows': 6, 'autocomplete': 'off'})

    def result(self):
        return Link(title=self.title.data,
                    slug=make_slug(self.title.data),
                    text=self.text.data,
                    url=self.url.data)


class SavedLink(Model):
    __table__ = 'saved_links'
    __fillable__ = ['user_id', 'link_id']
    __incrementing__ = False

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists('saved_links')
        with schema.create('saved_links') as table:
            table.big_integer('link_id').unsigned()
            table.integer('user_id').unsigned()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.index('link_id')
            table.index('user_id')
            table.primary(['link_id', 'user_id'])

    def __repr__(self):
        return '<SavedLink l:{} u:{}>'.format(self.link_id, self.user_id)

    @property
    def user(self):
        from news.models.user import User
        return User.by_id(self.user_id)

    @property
    def link(self):
        return Link.by_id(self.link_id)

    @classmethod
    def _cache_prefix(cls):
        return "sl:"

    @classmethod
    def by_user(cls, user):
        return cls.where('user_id', user.id).order_by('created_at', 'desc').get()

    def commit(self):
        try:
            self.save()
            # TODO
            # q.enqueue(_name_, self, result_ttl=0)
        except QueryException as e:
            print("already saved")
