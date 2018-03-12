from flask_wtf import Form
from orator.orm import belongs_to, has_many, morph_many
from slugify import slugify
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL

from news.lib.cache import cache
from news.lib.db.db import db, schema
from news.lib.db.time_filters import time_filters
from news.lib.utils.time_utils import time_ago
from news.models.report import Report


class Link(db.Model):
    __table__ = 'links'
    __fillable__ = ['title', 'slug', 'summary', 'user_id','url','feed_id']
    __guarded__ = ['id', 'reported','spam','archived','ups','downs']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('links')
        with schema.create('links') as table:
            table.big_increments('id')
            table.string('title', 128)
            table.string('slug', 150).unique()
            table.string('summary', 256)
            table.string('url', 128)
            table.big_integer('user_id')
            table.datetime('created_at')
            table.datetime('updated_at')
            table.foreign('user_id').references('id').on('users')
            table.big_integer('feed_id')
            table.foreign('feed_id').references('id').on('feeds')
            table.integer('ups').default(0)
            table.integer('downs').default(0)
            table.boolean('archived').default(False)
            table.integer('reported').default(0)
            table.boolean('spam').default(False)

    @belongs_to
    def feed(self):
        from news.models.feed import Feed
        return Feed

    @belongs_to
    def user(self):
        from news.models.user import User
        return User

    @has_many
    def votes(self):
        from news.models.vote import Vote
        return Vote

    @morph_many('reportable')
    def reports(self):
        return Report

    @classmethod
    def _cache_prefix(cls):
        return "l:"

    @classmethod
    def by_feed(cls, feed, sort, time):
        return Link.get_by_feed_id(feed.id, sort, time)

    @classmethod
    @cache.memoize()
    def get_by_feed_id(cls, feed_id, sort, time='all'):
        """
        Get's links by feed id and caches the result for future use
        :param feed_id: feed_id
        :param sort: sorting type: trending/new/best
        :param time: time filtering: day/week/month/year/all
        :return: list of links
        """
        q = Link.where('feed_id', feed_id)

        if time != 'all':
            q.where_raw(time_filters[time])

        # cache needs array of objects, not a orator collection
        res = [f for f in q.limit(1000).get()]
        return res

    def time_ago(self):
        return time_ago(self.created_at)

    def score(self):
        return self.ups - self.downs


class LinkForm(Form):
    title = StringField('Title', [DataRequired(), Length(max=128, min=6)])
    summary = StringField('Summary')
    url = StringField('Url', [DataRequired(), URL()])

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
