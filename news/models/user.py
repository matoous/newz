import bcrypt
from flask_login import current_user
from flask_wtf import Form
from orator.orm import belongs_to_many
from wtforms import StringField, PasswordField, SelectField, IntegerField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from news.lib.cache import cache
from news.lib.login import login_manager
from news.lib.db.db import db, schema


class User(db.Model):
    __table__ = 'users'
    __fillable__ = ['username', 'full_name', 'email', 'email_verified', 'subscribed', 'preferred_sorting', 'bio', 'url',
                    'profile_pic', 'p_show_images', 'p_min_link_score']
    __guarded__ = ['id', 'password', 'reported', 'spammer']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('users')
        with schema.create('users') as table:
            table.big_increments('id')
            table.string('username', 32).unique()
            table.string('full_name', 64).nullable()
            table.string('email', 128).unique()
            table.boolean('email_verified').default(False)
            table.boolean('subscribed').default(False)
            table.string('password', 128)
            table.integer('reported').default(0)
            table.boolean('spammer').default(False)
            table.datetime('created_at')
            table.datetime('updated_at')
            table.string('preferred_sorting', 10).default('trending')
            table.string('bio').nullable()
            table.string('url').nullable()
            table.string('profile_pic').nullable()
            table.integer('feed_subs').default(0)
            # preferences
            table.string('p_show_images', 1).default('y')
            table.integer('p_min_link_score').default(-3)
            # indexes
            table.index('username')
            table.index('email')

    def __repr__(self):
        return '<User %r>' % self.username

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.id == other.id

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, password):
        return bcrypt.checkpw(password, self.password)

    def get_id(self):
        return self.username

    @classmethod
    @cache.memoize()
    def by_name(cls, name):
        user = User.where('username', name).first()
        if user is not None:
            user.password = ''  #  don't save password in cache
        return user

    @staticmethod
    @login_manager.user_loader
    def load_user(session_id):
        return User.by_name(session_id)

    @classmethod
    def _cache_prefix(cls):
        return "u:"

    @belongs_to_many('feeds_users')
    def feeds(self):
        from news.models.feed import Feed
        return Feed

    @cache.memoize()
    def subscribed_feed_ids(self):
        return [feed.id for feed in self.feeds]

    def subscribed_to(self, feed):
        return feed.id in self.subscribed_feed_ids()

    def name(self):
        if self.full_name is not None:
            return self.full_name
        return self.username

    def subscribe(self, feed):
        if self.feed_subs >= 50:  # todo move to config, allow paying users to subscribe to more
            return False

        self.feeds().attach(feed)
        User.where('id', self.id).increment('feed_subs', 1) # todo update cache too
        cache.delete_memoized(self.subscribed_feed_ids)
        return True

    def unsubscribe(self, feed):
        self.feeds().detach(feed.id)
        User.where('id', self.id).decrement('feed_subs', 1) # todo update cache too
        cache.delete_memoized(self.subscribed_feed_ids)
        return True


class SignUpForm(Form):
    username = StringField('Username', [DataRequired()])
    email = EmailField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        users = User.where('username', self.username.data).or_where('email', self.email.data).get()
        if len(users) > 0:
            for user in users:
                if user.email == self.email.data:
                    self.email.errors.append('This email is already taken')
                if user.username == self.username.data:
                    self.username.errors.append('This username is already taken')
            return False

        if len(self.password.data) < 6:
            self.password.errors.append("Password must be at least 6 characters long")
            return False

        user = User(username=self.username.data, email=self.email.data)
        user.set_password(self.password.data)
        self.user = user
        return True


class LoginForm(Form):
    username_or_email = StringField('Username or email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        rv = Form.validate(self)

        self.user = None
        if not rv:
            return False
        if '@' in self.username_or_email.data:
            self.user = User.where('email', self.username_or_email.data).first()
        else:
            self.user = User.where('username', self.username_or_email.data).first()
        if self.user is None:
            self.errors['general'] = "Invalid username or password"
            return False
        return True


class SettingsForm(Form):
    show_images = SelectField('Show Images', choices=[('y', 'Always'), ('m', 'Homepage only'), ('n', 'Never')])
    min_link_score = IntegerField('Minimal link score')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        changes = {}
        if self.show_images.data != current_user.p_show_images:
            changes['p_show_images'] = self.show_images.data
        if self.min_link_score != current_user.p_min_link_score:
            changes['p_min_link_score'] = self.min_link_score.data
        return True
