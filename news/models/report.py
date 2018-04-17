from flask_wtf import Form
from orator import Model
from orator.orm import morph_to
from wtforms import TextAreaField
from wtforms.validators import Length

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

# TODO report form
class ReportForm(Form):
    comment = TextAreaField("Comment", [Length(max=2048)], render_kw={"placeholder": "Comment", "autocomplete": "off"})

    def validate(self):
        pass
