from flask_login import current_user
from flask_wtf import Form
from orator import Model
from orator.orm import has_many, belongs_to_many
from slugify import slugify

from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL

from news.lib.cache import cache
from news.lib.db.db import db, schema
from news.lib.sorts import hot
from news.models.link import Link
from news.models.vote import Vote


class Feed(Model):
    __table__ = 'feeds'
    __fillable__ = ['name', 'slug', 'description', 'default_sort', 'lang', 'over_18', 'logo']
    __guarded__ = ['id', 'reported']
    __hidden__ = ['reported']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('feeds')
        with schema.create('feeds') as table:
            table.increments('id').unsigned()
            table.string('name', 64)
            table.string('slug', 80).unique()
            table.string('description').nullable()
            table.string('default_sort', 12).default('trending')
            table.datetime('created_at')
            table.datetime('updated_at')
            table.string('lang', 12).default('en')
            table.boolean('over_18').default(False)
            table.string('logo', 128).nullable()
            table.boolean('reported').default(False)
            table.index('slug')

    @property
    def b_id(self):
        return self.id.to_bytes(8, 'big')

    def links_query(self, sort='trending'):
        return Link.by_feed(self, sort)

    @classmethod
    def by_slug(cls, slug):
        feed = Feed.where('slug', slug).first()
        return feed

    @classmethod
    def by_id(cls, id):
        f = cache.get('f:{}'.format(id))
        if f is not None:
            return f
        f = Feed.where('id', id).first()
        cache.set('f:{}'.format(id), f)
        return f

    @property
    def path(self):
        return "/f/%s/" % self.slug

    @classmethod
    def cache_prefix(cls):
        return "f:"

    @classmethod
    def by_id(cls, id):
        return Feed.where('id', id).first()

    @belongs_to_many('feeds_users')
    def users(self):
        from news.models.user import User
        return User


class FeedForm(Form):
    title = StringField('Title', [DataRequired(), Length(max=128, min=3)])
    description = StringField('Description', [DataRequired()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.feed = None

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        self.feed = Feed(name=self.title.data, description=self.description.data, slug=slugify(self.title.data))
        return True
