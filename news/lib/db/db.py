from orator import DatabaseManager, Model as BaseModel


class Orator(object):
    def __init__(self, app=None, manager_class=DatabaseManager):
        self.Model = BaseModel
        self.cli = None
        self._db = None
        self._manager_class = manager_class

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if 'ORATOR_DATABASES' not in app.config:
            raise RuntimeError('Missing "ORATOR_DATABASES" configuration')

        # Register request hooks
        self.register_handlers(app)

        # Getting config databases
        self._config = app.config['ORATOR_DATABASES']

        # Initializing database manager
        self._db = self._manager_class(self._config)

        self.Model.set_connection_resolver(self._db)

    def register_handlers(self, app):
        teardown = app.teardown_appcontext

        @teardown
        def disconnect(_):
            return self._db.disconnect()

    def __getattr__(self, item):
        return getattr(self._db, item)


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
    db = DatabaseManager(app.config['ORATOR_DATABASES'])
    from news.scripts.create_testing_data import create_default_feeds
    create_default_feeds()
