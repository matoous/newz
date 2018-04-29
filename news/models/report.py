from flask_wtf import Form
from orator import Model, accessor
from orator.orm import morph_to
from wtforms import TextAreaField, RadioField, IntegerField
from wtforms.validators import Length

from news.lib.db.db import schema


class Report(Model):
    __table__ = 'reports'
    __fillable__ = ['reason', 'comment', 'user_id', 'feed_id']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('reports')
        with schema.create('reports') as table:
            table.increments('id').unsigned()
            table.string('reason', 16)
            table.text('comment')
            table.integer('feed_id').unsigned()
            table.integer('user_id').unsigned()
            table.integer('reportable_id').unsigned()
            table.text('reportable_type')
            table.datetime('created_at')
            table.datetime('updated_at')
            table.index('user_id')
            table.index('feed_id')

    @morph_to
    def reportable(self):
        return

    @accessor
    def user(self):
        from news.models.user import User
        return User.by_id(self.user_id)

    @property
    def reported_thing(self):
        if self.reportable_type == "comments":
            return "comment"
        if self.reported_thing == "links":
            return "link"
        return None

    @accessor
    def thing(self):
        if self.reportable_type == "comments":
            from news.models.comment import Comment
            return Comment.by_id(self.reportable_id)
        if self.reportable_type == "links":
            from news.models.link import Link
            return Link.by_id(self.reportable_id)
        return None



class ReportForm(Form):
    comment = TextAreaField("Comment", [Length(max=2048)], render_kw={"placeholder": "Comment", "autocomplete": "off"})
    reason = RadioField("Reason", choices=[('breaks_rules',''),('spam',''), ('offensive', ''), ('other', '')])
    think_id = IntegerField("think_id")

    def validate(self):
        return True
