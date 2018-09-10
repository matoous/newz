from orator import Schema

from news.lib.db.db import db


class Action:
    """
    For logging admins action so other admins/gods can check
    """

    __table__ = 'actions'
    __fillable__ = ['action', 'data', 'user_id', 'feed_id']

    @classmethod
    def create_table(cls):
        schema = Schema(db)
        schema.drop_if_exists('actions')
        with schema.create('actions') as table:
            table.increments('id').unsigned()
            table.string('action', 16)
            table.text('data')
            table.integer('feed_id').unsigned()
            table.integer('user_id').unsigned()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.index('user_id')
            table.index('feed_id')
