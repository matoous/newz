from orator import accessor, Schema

from news.lib.db.db import db
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
        schema = Schema(db)
        schema.drop_if_exists(cls.__table__)
        with schema.create(cls.__table__) as table:
            table.boolean('god').default(False)
            table.integer('user_id').unsigned()
            table.foreign('user_id').references('id').on('users').on_delete('cascade')
            table.integer('feed_id').unsigned()
            table.foreign('feed_id').references('id').on('feeds').on_delete('cascade')
            table.datetime('created_at')
            table.datetime('updated_at')
            table.primary(['user_id', 'feed_id'])

    @accessor
    def user(self):
        from news.models.user import User
        if not 'user' in self._relations:
            self._relations['user'] = User.by_id(self.user_id)
        return self._relations['user']

    @accessor
    def feed(self):
        from news.models.feed import Feed
        if not 'feed' in self._relations:
            self._relations['feed'] = Feed.by_id(self.feed_id)
        return self._relations['feed']

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