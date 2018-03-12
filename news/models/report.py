from orator.orm import morph_to

from news.lib.db.db import db


class Report(db.Model):
    __table__ = 'reports'
    __fillable__ = ['reason', 'comment', 'by_user_id']

    @morph_to
    def reportable(self):
        return
