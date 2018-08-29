from typing import Optional

from flask_wtf import FlaskForm
from orator import mutator, Schema
from orator.orm import belongs_to_many
from rq.decorators import job
from slugify import slugify
from wtforms import StringField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length
from markdown2 import markdown

from news.lib.cache import cache
from news.lib.db.db import db
from news.lib.task_queue import redis_conn, q
from news.lib.solr import add_feed_to_search
from news.lib.utils.slugify import make_slug
from news.models.base import Base
from news.models.base_form import BaseForm
from news.models.link import Link


class Feed(Base):
    __table__ = 'feeds'
    __fillable__ = ['id', 'name', 'img', 'slug', 'description', 'default_sort', 'rules', 'lang', 'over_18', 'logo', 'reported', 'subscribers_count']
    __searchable__ = ['id', 'name', 'description', 'lang', 'over_18', 'created_at']

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists(cls.__table__)
        with schema.create(cls.__table__) as table:
            table.increments('id').unsigned()
            table.string('name', 64)
            table.string('slug', 80).unique()
            table.text('description').nullable()
            table.text('rules').nullable()
            table.text('img').nullable()
            table.integer('subscribers_count').default(0)
            table.string('default_sort', 12).default('trending')
            table.datetime('created_at')
            table.datetime('updated_at')
            table.string('lang', 12).default('en')
            table.boolean('over_18').default(False)
            table.string('logo', 128).nullable()
            table.boolean('reported').default(False)
            table.index('slug')

    def __init__(self, **attributes):
        super().__init__(**attributes, over_18=False, lang='en')

    @property
    def b_id(self):
        return self.id.to_bytes(8, 'big')

    def links_query(self, sort: str = 'trending') -> Link:
        return Link.by_feed(self, sort)

    @classmethod
    def by_slug(cls, slug: str) -> Optional['Feed']:
        """
        Get feed by slug
        :param username: slug
        :return:
        """
        cache_key = 'fslug:{}'.format(slug)

        # check feed slug cache
        in_cache = cache.get(cache_key, raw=True)
        uid = int(in_cache) if in_cache else None

        # return user on success
        if uid is not None:
            return Feed.by_id(uid)

        # try to load user from DB on failure
        feed = Feed.where('slug', slug).first()

        # cache the result
        if feed is not None:
            cache.set(cache_key, feed.id, raw=True)
            feed.write_to_cache()

        return feed

    @classmethod
    def by_id(cls, id: str) -> 'Feed':
        """
        Find feed by id
        :param id: id
        :return: feed or None
        """
        f = cls.load_from_cache(id)

        # return cached result if possible
        if f is not None:
            return f

        # try to find feed in DB
        f = Feed.where('id', id).first()

        # cache the result
        if f is not None:
            f.write_to_cache()

        return f

    @property
    def url(self) -> str:
        return "/f/{}".format(self.slug)

    @property
    def route(self) -> str:
        return "/f/{}".format(self.slug)

    @classmethod
    def _cache_prefix(cls):
        return "f:"

    @belongs_to_many('feeds_users')
    def users(self):
        from news.models.user import User
        return User

    @mutator
    def rules(self, value):
        rules = markdown(value, safe_mode="escape")
        cache.set(self.rules_cache_key, rules)
        self.set_raw_attribute('rules', value)

    @property
    def rules_cache_key(self):
        return "rules:{}".format(self.id)

    @property
    def rules_html(self):
        rules = cache.get(self.rules_cache_key)
        if rules is None:
            rules = markdown(self.rules) if self.rules else ""
            cache.set(self.rules_cache_key, rules)
        return rules

    def commit(self):
        self.save()
        q.enqueue(handle_new_feed, self, result_ttl=0)


class FeedForm(BaseForm):
    name = StringField('Name', [DataRequired(), Length(max=128, min=3)])
    description = TextAreaField('Description', [DataRequired(), Length(max=8192)], render_kw={'placeholder': 'Feed description', 'rows': 6, 'autocomplete': 'off'})
    rules = TextAreaField('Rules', [DataRequired(), Length(max=8192)], render_kw={'placeholder': 'Feed rules', 'rows': 6, 'autocomplete': 'off'})

    def fill(self, feed: Feed):
        self.name.data = feed.name
        self.description.data = feed.description
        self.rules.data = feed.rules

    def result(self) -> Feed:
        return Feed(name=self.name.data, description=self.description.data, slug=make_slug(self.name.data))


class EditFeedForm(FlaskForm):
    description = TextAreaField('Description', [DataRequired(), Length(max=8192)], render_kw={'placeholder': 'Feed description', 'rows': 6, 'autocomplete': 'off'})
    rules = TextAreaField('Rules', [Length(max=8192)], render_kw={'placeholder': 'Feed rules', 'rows': 6, 'autocomplete': 'off'})
    img = FileField('Logo')

    def fill(self, feed):
        self.description.data = feed.description
        self.rules.data = feed.rules


@job('medium', connection=redis_conn)
def handle_new_feed(feed):
    add_feed_to_search(feed)
    return None