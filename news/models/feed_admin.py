from news.lib.db.db import db


class FeedAdmin(db.Model):
    __table__ = 'feed_admins'
    __fillable__ = ['super_admin', 'user_id', 'feed_id']
