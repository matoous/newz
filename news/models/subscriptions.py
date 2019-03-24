from orator import Schema

from news.lib.db.db import db


def create_subscriptions_table():
    """
    Create table for feed subscriptions
    """
    schema = Schema(db)
    schema.drop_if_exists("feeds_users")
    with schema.create("feeds_users") as table:
        table.integer("feed_id").unsigned()
        table.foreign("feed_id").references("id").on("feeds").ondelete("cascade")
        table.integer("user_id").unsigned()
        table.foreign("user_id").references("id").on("users").ondelete("cascade")
        table.index("feed_id")
        table.index("user_id")
        table.primary(["user_id", "feed_id"])
