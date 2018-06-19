from flask_wtf import Form
from orator import accessor
from wtforms import SelectField, HiddenField, TextAreaField
from wtforms.validators import DataRequired

from news.lib.cache import conn
from news.lib.db.db import schema
from news.models.base import Base


class Ban(Base):
    __table__ = 'bans'
    __fillable__ = ['reason', 'feed_id', 'user_id', 'until']
    __incrementing__ = False

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('bans')
        with schema.create('bans') as table:
            table.string('reason')
            table.integer('user_id').unsigned()
            table.integer('feed_id').unsigned()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.datetime('until')
            table.primary(['feed_id','user_id'])

    @classmethod
    def _cache_prefix(cls):
        return "ban:"

    @property
    def id(self):
        return "{feed}:{user}".format(feed=self.feed_id, user=self.user_id)

    @accessor
    def user(self):
        from news.models.user import User
        return User.by_id(self.user_id)

    @classmethod
    def cache_key(cls, user_id, feed_id):
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
        conn.set(self.id, 'y')

    @classmethod
    def by_user_and_feed(cls, user, feed):
        return cls.by_user_and_feed_id(user.id, feed.id)

    @classmethod
    def by_user_and_feed_id(cls, user_id, feed_id):
        return conn.get(cls.cache_key(user_id, feed_id))

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


class BanForm(Form):
    user_id = HiddenField('User Id', [DataRequired()])
    reason = TextAreaField('Reason', [DataRequired()])
    duration = SelectField(
        'Duration',
        choices=[('week', 'Week'), ('month', 'Month'), ('3months', '3 months'), ('6months', '6 months'), ('year', 'Year')]
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