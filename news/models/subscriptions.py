from news.lib.db.db import schema


def create_subscriptions_table():
    schema.drop_if_exists('feeds_users')
    with schema.create('feeds_users') as table:
        table.big_integer('feed_id')
        table.big_integer('user_id')
        #
        table.primary('feed_id')
        table.primary('user_id')
        table.index('feed_id')
        table.index('user_id')