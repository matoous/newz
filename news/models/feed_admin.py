from orator import accessor

from news.lib.db.db import schema
from news.models.base import Base


class FeedAdmin(Base):
    """
    FeedAdmin model
    """

    __table__ = 'feed_admins'
    __fillable__ = ['id', 'god', 'user_id', 'feed_id']
    __incrementing__ = False

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('feed_admins')
        with schema.create('feed_admins') as table:
            table.boolean('god').default(False)
            table.integer('user_id').unsigned()
            table.integer('feed_id').unsigned()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.primary(['user_id', 'feed_id'])

    @accessor
    def user(self):
        from news.models.user import User
        return User.by_id(self.user_id)

    @accessor
    def feed(self):
        from news.models.feed import Feed
        return Feed.by_id(self.feed_id)

    @classmethod
    def by_feed_id(cls, feed_id):
        # TODO caching
        """
        Find feed admins by feed id
        :param feed_id: feed id
        :return: feed admins
        """
        return cls.where('feed_id', feed_id).get()

    @classmethod
    def by_user_id(cls, user_id):
        # TODO caching
        """
        Finds users administrations for feeds
        :param user_id: user_id
        :return: feed administrations
        """
        return cls.where('user_id', user_id).get()

    @classmethod
    def by_user_and_feed_id(cls, user_id, feed_id):
        # TODO caching
        """
        Finds single feed administration by user and feed id
        :param user_id: user id
        :param feed_id: feed id
        :return: feed administration
        """
        return cls.where('user_id', user_id).where('feed_id', feed_id).first()