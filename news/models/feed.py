from flask_login import current_user
from flask_wtf import Form
from orator.orm import has_many
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
            table.char('name', 64)
            table.char('slug', 80).unique()
            table.string('description').nullable()
            table.char('default_sorting', 12).default('new')
            table.datetime('created_at')
            table.datetime('updated_at')
            table.char('lang', 12).default('en')
            table.boolean('over_18').default(False)
            table.char('logo', 128).nullable()
            table.boolean('reported').default(False)
            table.index('slug')

    @has_many
    def links(self):
        return Link

    @classmethod
    def by_slug(cls, slug, sorting='hot'):
        feed = Feed.where('slug',slug).with_({
                    'links': Link.with_({
                        'votes': Vote.query().where('user_id', current_user.id)
                    }).order_by('created_at','desc').limit(10)
                }).first()
        feed.links = sorted(feed.links, key=lambda x: hot(x.score, x.created_at), reverse=True)
        return feed

    @property
    def path(self):
        return "/f/%s/" % self.slug

    @classmethod
    def _cache_prefix(cls):
        return "f:"


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
