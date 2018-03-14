from orator import Model
from orator.orm import has_many, morph_many
from news.lib.adding import add_to_queries
from news.lib.cache import cache
from news.lib.db.db import db, schema
from news.lib.queue import q
from news.lib.utils.time_utils import time_ago
from news.models.report import Report


class Comment(Model):
    __table__ = 'comments'
    __fillable__ = ['parent_id', 'text', 'user_id', 'link_id']
    __guarded__ = ['id', 'reported', 'spam', 'archived', 'ups', 'downs']
    __hidden__ = ['reported', 'spam']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('links')
        with schema.create('links') as table:
            table.big_increments('id')
            table.string('title', 128)
            table.string('slug', 150).unique()
            table.string('summary', 256)

    def __eq__(self, other):
        if not isinstance(other, Comment):
            return False
        return other.id == self.id

    def __repr__(self):
        return '<Comment {}>'.format(self.id)

    @property
    def link(self):
        from news.models.link import Link
        return Link.by_id(self.link_id)

    @property
    def user(self):
        from news.models.user import User
        return User.by_id(self.user_id)

    @has_many
    def votes(self):
        from news.models.vote import Vote
        return Vote

    @property
    def num_votes(self):
        return self.ups + self.downs

    @morph_many('reportable')
    def reports(self):
        return Report

    @classmethod
    def _cache_prefix(cls):
        return "c:"

    def time_ago(self):
        return time_ago(self.created_at)

    @property
    def score(self):
        return self.ups - self.downs

    def commit(self):
        self.save()
        self.ups = self.downs = 0
        q.enqueue(add_to_queries, self, result_ttl=0)