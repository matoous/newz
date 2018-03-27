from news.lib.db.db import db, schema


class FeedAdmin(db.Model):
    __table__ = 'feed_admins'
    __fillable__ = ['god', 'user_id', 'feed_id']

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

    def __init__(self, user, feed, god=False):
        self.user_id = user.id
        self.feed_id = feed.id
        self.god = god

    @classmethod
    def by_feed_id(cls, feed_id):
        return cls.where('feed_id', feed_id).get()

    @classmethod
    def by_user_id(cls, user_id):
        return cls.where('user_id', user_id).get()
