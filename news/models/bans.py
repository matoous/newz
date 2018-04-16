from orator import Model

from news.lib.db.db import schema


class Ban(Model):
    __table__ = 'reports'
    __fillable__ = ['reason', 'feed_id', 'user_id']
    __incrementing__ = False

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('reports')
        with schema.create('reports') as table:
            table.string('reason')
            table.integer('user_id').unsigned()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.index(['feed_id','user_id'])


