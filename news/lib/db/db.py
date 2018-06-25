from flask_orator import Orator


db = Orator()

def create_tables(app):
    with app.app_context():
        from news.models.token import DisposableToken
        DisposableToken.create_table()

        from news.models.feed import Feed
        Feed.create_table()

        from news.models.user import User
        User.create_table()

        from news.models.link import Link
        Link.create_table()

        from news.models.vote import LinkVote
        LinkVote.create_table()

        from news.models.comment import Comment
        Comment.create_table()

        from news.models.vote import CommentVote
        CommentVote.create_table()

        from news.models.subscriptions import create_subscriptions_table
        create_subscriptions_table()

        from news.models.feed_admin import FeedAdmin
        FeedAdmin.create_table()

        from news.models.report import Report
        Report.create_table()

        from news.models.link import SavedLink
        SavedLink.create_table()

        from news.models.ban import Ban
        Ban.create_table()

def init_data(app):
    from news.scripts.create_testing_data import create_default_feeds
    create_default_feeds()