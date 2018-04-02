from flask_wtf import Form
from orator import Model
from orator.orm import belongs_to, has_many, morph_many
from rq.decorators import job
from slugify import slugify
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, URL

from news.lib.cache import cache
from news.lib.db.db import db, schema
from news.lib.db.query import add_to_queries
from news.lib.db.sorts import sorts
from news.lib.queue import q, redis_conn
from news.lib.sorts import hot
from news.lib.utils.time_utils import time_ago, epoch_seconds
from news.models.base import Base
from news.models.report import Report

MAX_IN_CACHE = 1000


class Link(Base):
    __table__ = 'links'
    __fillable__ = ['title', 'slug', 'summary', 'text', 'user_id', 'url', 'feed_id']
    __guarded__ = ['id', 'reported', 'spam', 'archived', 'ups', 'downs', 'comments_count']
    __hidden__ = ['reported', 'spam']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('links')
        with schema.create('links') as table:
            table.big_increments('id').unsigned()
            table.string('title', 128)
            table.string('slug', 150).unique()
            table.text('summary')
            table.text('text')
            table.text('url')
            table.integer('user_id').unsigned()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.foreign('user_id').references('id').on('users')
            table.integer('feed_id').unsigned()
            table.foreign('feed_id').references('id').on('feeds')
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

    @property
    def hot(self):
        return hot(self.score, self.created_at)

    @property
    def feed(self):
        from news.models.feed import Feed
        return Feed.by_id(self.feed_id)

    @classmethod
    def by_id(cls, id):
        cache_key = cls._cache_key_from_id(id)
        cached_data = cache.get(cache_key)
        if cached_data is None:
            cached_data = cls.where('id', id).first()
            cached_data.write_to_cache()
        return cached_data

    @property
    def user(self):
        from news.models.user import User
        return User.by_id(self.user_id)

    @property
    def trimmed_summary(self):
        if len(self.summary) > 300:
            return self.summary[:300] + '...'
        return self.summary

    @property
    def votes(self):
        from news.models.vote import LinkVote
        return LinkVote.where('link_id', self.id).get()

    def vote_by(self, user):
        from news.models.vote import LinkVote
        if user.is_anonymous:
            return None
        return LinkVote.by_link_and_user(self.id, user.id)

    @property
    def num_votes(self):
        return self.ups + self.downs

    @morph_many('reportable')
    def reports(self):
        return Report

    @classmethod
    def by_feed(cls, feed, sort):
        return Link.get_by_feed_id(feed.id, sort)

    @classmethod
    def get_by_feed_id(cls, feed_id, sort):
        cache_key = 'fs:{}.{}'.format(feed_id, sort)

        r = cache.get(cache_key)
        if r is not None:
            return r

        q = Link.where('feed_id', feed_id).order_by_raw(sorts[sort])

        # cache needs array of objects, not a orator collection
        res = [f for f in q.limit(1000).get()]
        cache.set(cache_key, res)
        return res

    def time_ago(self):
        return time_ago(self.created_at)

    @property
    def score(self):
        return self.ups - self.downs

    def commit(self):
        self.save()
        q.enqueue(add_to_queries, self, result_ttl=0)


class LinkForm(Form):
    title = StringField('Title', [DataRequired(), Length(max=128, min=6)], render_kw={'placeholder': 'Title', 'autocomplete': 'off'})
    url = StringField('Url', [DataRequired(), URL(), Length(max=256)], render_kw={'placeholder': 'URL', 'oninput': 'handleUrlChange()', 'autocomplete': 'off'})
    summary = TextAreaField('Summary', [Length(max=8192)], render_kw={'placeholder': 'Summary or text', 'rows': 6, 'autocomplete': 'off'})

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.link = None

    def validate(self, feed, user):
        rv = Form.validate(self)
        if not rv:
            return False
        self.link = Link(title=self.title.data,
                         slug=slugify(self.title.data),
                         summary=self.summary.data,
                         url=self.url.data,
                         feed_id=feed.id,
                         user_id=user.id)
        return True


class SavedLink(Model):
    __table__ = 'saved_links'
    __fillable__ = ['user_id', 'link_id']

    @classmethod
    def create_table(cls):
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
    def by_feed(cls, user):
        return cls.where('user_id', user.id).get()

    def commit(self):
        self.save()
        # TODO
        # q.enqueue(_name_, self, result_ttl=0)
