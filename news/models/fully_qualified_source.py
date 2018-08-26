from datetime import datetime, timedelta

import feedparser
from orator import Schema, accessor, mutator
from slugify import slugify

from news.lib.db.db import db
from news.lib.utils.slugify import make_slug, remove_html_tags
from news.models.base import Base


class FullyQualifiedSource(Base):
    """Fully Qualified Sources are RSS feeds from which the links are automatically posted to given feed

    Fully Qualified Sources (FQS) are periodically checked, new/not yet posted links are parsed and than posted
    to the feed. These automatically posted links are editable by admins which allows correction of mistakes
    such as badly trimmed titles, missing descriptions etc.

    Args:
        feed_id (int): Id of feed to which this FQS belongs
        url (string): RSS feed URL
        update_interval (timedelta): Time between automatic checks
    """
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

    @classmethod
    def _cache_prefix(cls):
        return "fqs:"

    @accessor
    def update_interval(self) -> timedelta:
        return timedelta(seconds=self.get_raw_attribute('update_interval'))

    @mutator
    def update_interval(self, value: timedelta):
        self.set_raw_attribute('update_interval', value.total_seconds())

    def should_update(self) -> bool:
        """
        Should be feed be updated?
        :return:
        """
        return self.updated_at + self.update_interval > datetime.now()

    @property
    def feed(self):
        """
        Return feed to which this FQS belongs.
        Caches the result in FQS relations.
        :return: Feed
        """
        from news.models.feed import Feed
        if 'feed' not in self._relations:
            self._relations['feed'] = Feed.by_id(self.feed_id)
        return self._relations['feed']

    def get_links(self):
        d = feedparser.parse(self.url)

        res = []
        for entry in d['entries']:
            # get the link text
            text = remove_html_tags(entry['summary']) if 'summary' in entry else ''
            if len(text) > 300:
                if 'content' in entry:
                    for e in entry['content']:
                        if 'value' in e and len(e['value']) < 300:
                            text = remove_html_tags(e['value'])
            if len(text) > 300:
                idx = text.rfind('. ', 0, 300)
                text = text[:idx + 1]

            #img?
            if 'links' in entry:
                for link in entry['links']:
                    if link['type'] == 'image/jpeg':
                        print(link)

            # title
            title = entry['title']
            if len(title) > 128:
                idx = title.rfind(' ', 0, 128)
                title = title[:idx]

            res.append({'title': title,
                        'slug': make_slug(title),
                        'text': text,
                        'url': entry['link'],
                        'feed_id': self.feed.id})
        return res
