from flask_login import current_user
from flask_wtf import Form
from orator.orm import has_many, belongs_to_many
from slugify import slugify

from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL

from news.lib.db.db import db, schema
from news.lib.sorts import hot
from news.models.link import Link
from news.models.vote import Vote


class Feed(db.Model):
    __table__ = 'feeds'
    __fillable__ = ['name', 'slug', 'description', 'default_sorting', 'lang','over_18','logo']
    __guarded__ = ['id','reported']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('feeds')
        with schema.create('feeds') as table:
            table.big_increments('id')
            table.string('name', 64)
            table.string('slug', 80).unique()
            table.string('description').nullable()
            table.string('default_sorting', 12).default('new')
            table.datetime('created_at')
            table.datetime('updated_at')
            table.string('lang', 12).default('en')
            table.boolean('over_18').default(False)
            table.string('logo', 128).nullable()
            table.boolean('reported').default(False)
            table.index('slug')

    @has_many
    def links(self):
        return Link

    def links_query(self, sort='trending', time='day'):
        return Link.by_feed(self, sort, time)

    @classmethod
    def by_slug(cls, slug, sort='trending'):
        feed = Feed.where('slug', slug).first()
        return feed
        #votes_query = {'votes': Vote.query().where('user_id', current_user.id)}
        #feed = Feed.where('slug', slug).with_({
        #    'links': Link.with_(votes_query).order_by('created_at', 'desc').limit(10)
        #}).first()

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
