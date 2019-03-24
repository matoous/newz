from flask_wtf import FlaskForm
from orator import Model, accessor, Schema
from orator.orm import morph_to
from wtforms import TextAreaField, RadioField, IntegerField
from wtforms.validators import Length, Required, DataRequired

from news.lib.db.db import db


class Report(Model):
    __table__ = "reports"
    __fillable__ = ["reason", "comment", "user_id", "feed_id"]

    @classmethod
    def create_table(cls):
        """
        Create table for reports
        """
        schema = Schema(db)
        schema.drop_if_exists("reports")
        with schema.create("reports") as table:
            table.increments("id").unsigned()
            table.string("reason", 16)
            table.text("comment")
            table.integer("feed_id").unsigned()
            table.foreign("feed_id").references("id").on("feeds").ondelete("cascade")
            table.integer("user_id").unsigned()
            table.foreign("user_id").references("id").on("users").ondelete("cascade")
            table.integer("reportable_id").unsigned()
            table.text("reportable_type")
            table.datetime("created_at")
            table.datetime("updated_at")
            table.index("user_id")
            table.index("feed_id")

    @morph_to
    def reportable(self):
        return

    @accessor
    def user(self) -> "User":
        """
        Get report author
        :return: author of report
        """
        from news.models.user import User

        if "user" not in self._relations:
            self._relations["user"] = User.by_id(self.user_id)
        return self._relations["user"]

    @property
    def reported_thing(self):
        if self.reportable_type == "comments":
            return "comment"
        if self.reportable_type == "links":
            return "link"
        return None

    @accessor
    def thing(self):
        if "thing" not in self._relations:
            if self.reportable_type == "comments":
                from news.models.comment import Comment

                self._relations["thing"] = Comment.by_id(self.reportable_id)
            if self.reportable_type == "links":
                from news.models.link import Link

                self._relations["thing"] = Link.by_id(self.reportable_id)
        return self._relations["thing"]


class ReportForm(FlaskForm):
    comment = TextAreaField(
        "Comment",
        [Length(max=2048)],
        render_kw={"placeholder": "Comment", "autocomplete": "off"},
    )
    reason = RadioField(
        "Reason",
        choices=[("breaks_rules", ""), ("spam", ""), ("offensive", ""), ("other", "")],
    )
    think_id = IntegerField("think_id", [DataRequired()])

    def result(self):
        return Report(reason=self.reason.data, comment=self.comment.data)
