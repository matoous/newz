from orator import Schema

from news.lib.db.db import db


def create_subscriptions_table():
    schema = Schema(db)
    schema.drop_if_exists('feeds_users')
    with schema.create('feeds_users') as table:
        table.integer('feed_id').unsigned()
        table.integer('user_id').unsigned()
        table.index('feed_id')
        table.index('user_id')
        table.primary(['user_id', 'feed_id'])
