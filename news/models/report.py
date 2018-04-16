from orator import Model
from orator.orm import morph_to

from news.lib.db.db import schema


class Report(Model):
    __table__ = 'reports'
    __fillable__ = ['reason', 'comment', 'user_id']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('reports')
        with schema.create('reports') as table:
            table.increments('id').unsigned()
            table.string('reason')
            table.string('comment')
            table.integer('user_id').unsigned()
            table.datetime('created_at')
            table.datetime('updated_at')
            table.index('user_id')

    @morph_to
    def reportable(self):
        return
