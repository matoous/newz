from datetime import datetime, timedelta

import feedparser
from orator import Schema, accessor, mutator
from slugify import slugify

from news.lib.db.db import db
from news.lib.utils.slugify import make_slug, remove_html_tags
from news.models.base import Base


class FullyQualifiedSource(Base):
    __table__ = 'fqs'
    __fillable__ = ['id', 'feed_id', 'url', 'update_interval', 'updated_at', 'created_at', 'next_update']

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists('fqs')
        with schema.create('fqs') as table:
            table.increments('id').unsigned()
            table.text('url').unique()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.datetime('next_update')
            table.integer('update_interval')
            table.integer('feed_id').unsigned()
            table.foreign('feed_id').references('id').on('feeds').ondelete('cascade')

    @accessor
    def update_interval(self) -> timedelta:
        return timedelta(seconds=self.get_raw_attribute('update_interval'))

    @mutator
    def update_interval(self, value: timedelta):
        self.set_raw_attribute('update_interval', value.total_seconds())

    def should_update(self) -> bool:
        return self.updated_at + self.update_interval > datetime.now()

    @accessor
    def feed(self):
        from news.models.feed import Feed
        if not 'feed' in self._relations:
            self._relations['feed'] = Feed.by_id(self.feed_id)
        return self._relations['feed']

    def get_links(self):
        d = feedparser.parse(self.url)
        return [{'title': entry['title'],
                 'slug': make_slug(entry['title']),
                 'text': remove_html_tags(entry['summary']) if 'summary' in entry else '',
                 'url': entry['link'],
                 'feed_id': self.feed.id} for entry in d['entries'] if len(entry['title']) < 128]
