from flask_wtf import Form
from orator.orm import belongs_to
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL

from news.lib.db.db import db, schema
from news.lib.utils.time_utils import time_ago


class Link(db.Model):
    __table__ = 'links'
    __fillable__ = ['title', 'slug', 'summary', 'user_id','url','feed_id']
    __guarded__ = ['id', 'reported','spam','archived','score']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('links')
        with schema.create('links') as table:
            table.big_increments('id')
            table.char('title', 128)
            table.char('slug', 150).unique()
            table.char('summary', 256)
            table.char('url', 128)
            table.big_integer('user_id')
            table.foreign('user_id').references('id').on('users')
            table.big_integer('feed_id')
            table.foreign('feed_id').references('id').on('feeds')
            table.integer('score').default(0)
            table.boolean('archived').default(False)
            table.boolean('reported').default(False)
            table.boolean('spam').default(False)

    @belongs_to
    def feed(self):
        from news.models.feed import Feed
        return Feed

    @classmethod
    def _cache_prefix(cls):
        return "l:"

    def time_ago(self):
        return time_ago(self.posted)


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
        self.link = Link(self.title.data, self.summary.data, self.url.data, feed, user)
        return True
