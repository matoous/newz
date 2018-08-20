from news.models.ban import Ban
from news.models.comment import Comment
from news.models.feed import Feed
from news.models.feed_admin import FeedAdmin
from news.models.link import Link
from news.models.report import Report
from news.models.subscriptions import create_subscriptions_table
from news.models.token import DisposableToken
from news.models.user import User
from news.models.vote import CommentVote, LinkVote


def create_tables():
    User.create_table()
    Feed.create_table()
    Link.create_table()
    Ban.create_table()
    Comment.create_table()
    FeedAdmin.create_table()
    Report.create_table()
    create_subscriptions_table()
    DisposableToken.create_table()
    CommentVote.create_table()
    LinkVote.create_table()