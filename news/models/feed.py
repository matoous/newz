from flask_wtf import Form
from orator.orm import belongs_to_many
from slugify import slugify
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length

from news.lib.db.db import schema
from news.models.base import Base
from news.models.link import Link


class Feed(Base):
    __table__ = 'feeds'
    __fillable__ = ['id', 'name', 'slug', 'description', 'default_sort', 'lang', 'over_18', 'logo', 'reported']

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
        f = cls.load_from_cache(id)
        if f is not None:
            return f
        f = Feed.where('id', id).first()
        if f is not None:
            f.write_to_cache()
        return f

    @property
    def path(self):
        return "/f/%s/" % self.slug

    @classmethod
    def _cache_prefix(cls):
        return "f:"

    @belongs_to_many('feeds_users')
    def users(self):
        from news.models.user import User
        return User


class FeedForm(Form):
    name = StringField('Name', [DataRequired(), Length(max=128, min=3)])
    description = TextAreaField('Description', [DataRequired(), Length(max=8192)], render_kw={'placeholder': 'Feed description', 'rows': 6, 'autocomplete': 'off'})

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.feed = None

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        self.feed = Feed(name=self.name.data, description=self.description.data, slug=slugify(self.name.data))
        return True

    def fill(self, feed):
        self.name.data = feed.name
        self.description.data = feed.description