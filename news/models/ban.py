from orator import Schema
from wtforms import SelectField, HiddenField, TextAreaField
from wtforms.validators import DataRequired

from news.lib.cache import cache
from news.lib.db.db import db
from news.models.base import Base
from news.models.base_form import BaseForm


class Ban(Base):
    """
    Ban user
    Bans are issued per user per feed
    Bans are permanently cached in redis, so they need to do be loaded in case of cache failure
    """
    __table__ = 'bans'
    __fillable__ = ['reason', 'feed_id', 'user_id', 'until']
    __incrementing__ = False

    @classmethod
    def create_table(cls):
        """
        Create table for bans
        """
        schema = Schema(db)
        schema.drop_if_exists('bans')
        with schema.create('bans') as table:
            table.string('reason')
            table.integer('user_id').unsigned()
            table.foreign('user_id').references('id').on('users').on_delete('cascade')
            table.integer('feed_id').unsigned()
            table.foreign('feed_id').references('id').on('feeds').on_delete('cascade')
            table.datetime('created_at')
            table.datetime('updated_at')
            table.datetime('until')
            table.primary(['feed_id', 'user_id'])

    @classmethod
    def _cache_prefix(cls):
        """
        Bans cache prefix
        :return: 'ban'
        """
        return 'ban:'

    @property
    def id(self) -> str:
        return "{feed}:{user}".format(feed=self.feed_id, user=self.user_id)

    @property
    def user(self) -> 'User':
        from news.models.user import User
        if 'user' not in self._relations:
            self._relations['user'] = User.by_id(self.user_id)
        return self._relations['user']

    @property
    def feed(self) -> 'Feed':
        from news.models.feed import Feed
        if 'feed' not in self._relations:
            self._relations['feed'] = Feed.by_id(self.feed_id)
        return self._relations['feed']

    @classmethod
    def cache_key(cls, user_id, feed_id) -> str:
        return "{feed}:{user}".format(feed=feed_id, user=user_id)

    def apply(self, user=None, feed=None):
        if user is None:
            from news.models.user import User
            user = User.by_id(self.user_id)

        if feed is None:
            from news.models.feed import Feed
            feed = Feed.by_id(self.feed_id)

        # can't ban admin
        if user.is_feed_admin(feed):
            return False

        user.unsubscribe(feed)

        self.save()
        self.write_to_cache()

    def write_to_cache(self):
        cache.set(self.id, 'y')

    @classmethod
    def by_user_and_feed(cls, user, feed):
        return cls.by_user_and_feed_id(user.id, feed.id)

    @classmethod
    def by_user_and_feed_id(cls, user_id, feed_id):
        return cache.get(cls.cache_key(user_id, feed_id))

    @classmethod
    def by_user(cls, user):
        return cls.by_user_id(user.id)

    @classmethod
    def by_user_id(cls, user_id):
        return cls.where('user_id', user_id).get()

    @classmethod
    def by_feed(cls, feed):
        return cls.by_user_id(feed.id)

    @classmethod
    def by_feed_id(cls, feed_id):
        return cls.where('user_id', feed_id).get()


class BanForm(BaseForm):
    user_id = HiddenField('User Id', [DataRequired()])
    reason = TextAreaField('Reason', [DataRequired()])
    duration = SelectField(
        'Duration',
        choices=[('week', 'Week'), ('month', 'Month'), ('3months', '3 months'), ('6months', '6 months'),
                 ('year', 'Year')]
    )

    def get_duration(self):
        if self.duration.data == 'week':
            return 7 * 24 * 60 * 60
        elif self.duration.data == 'month':
            return 24 * 60 * 60 * 31
        elif self.duration.data == '3months':
            return 24 * 60 * 60 * 31 * 3
        elif self.duration.data == '6months':
            return 24 * 60 * 60 * 31 * 6
        elif self.duration.data == 'year':
            return 24 * 60 * 60 * 365
        else:
            return 24 * 60 * 60

    def fill(self, user):
        self.user_id.data = user.id
