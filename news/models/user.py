from datetime import datetime
from secrets import token_urlsafe

from flask_login import current_user, login_user, logout_user
from flask_wtf import Form
from orator import accessor
from orator.orm import belongs_to_many, has_many
from passlib.hash import bcrypt
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField, HiddenField
from wtforms.fields.html5 import EmailField, URLField
from wtforms.validators import DataRequired, URL, Length

from news.config.config import GODS
from news.lib.cache import cache
from news.lib.db.db import schema
from news.lib.login import login_manager
from news.lib.mail import reset_email, send_mail
from news.lib.queue import redis_conn, q
from news.lib.verifications import EmailVerification
from news.models.base import Base
from news.models.feed_admin import FeedAdmin
from news.models.token import DisposableToken

MAX_SUBSCRIPTIONS_FREE = 50


class User(Base):
    __table__ = 'users'
    __fillable__ = ['id', 'password', 'reported', 'spammer', 'username', 'full_name', 'email', 'email_verified', 'subscribed', 'preferred_sort', 'bio', 'url',
                    'profile_pic', 'email_public'
                    'p_show_images', 'p_min_link_score']
    __hidden__ = ['password']
    __append__ = ['session_token']
    __searchable__ = ['id', 'username', 'full_name']


    @classmethod
    def create_table(cls):
        schema.drop_if_exists('users')
        with schema.create('users') as table:
            table.increments('id').unsigned()
            table.string('username', 32).unique()
            table.string('full_name', 64).nullable()
            table.string('email', 128).unique()
            table.boolean('email_verified').default(False)
            table.boolean('subscribed').default(False)
            table.boolean('email_public').default(False)
            table.string('password', 128)
            table.integer('reported').default(0)
            table.boolean('spammer').default(False)
            table.datetime('created_at')
            table.datetime('updated_at')
            table.string('preferred_sort', 10).default('trending')
            table.text('bio').nullable()
            table.text('url').nullable()
            table.text('profile_pic').nullable()
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

    @property
    def name(self):
        if self.full_name is not None:
            return self.full_name
        return self.username

    def set_password(self, password):
        self.set_attribute('password', bcrypt.hash(password))

    def check_password(self, password):
        return bcrypt.verify(password, self.password)

    def get_id(self):
        if self.session_token is not None:
            return self.session_token
        return ''

    @accessor
    def session_token(self):
        return self._accessor_cache['session_token']

    def login(self):
        token = DisposableToken.get()
        self._accessor_cache["session_token"] = token.id
        cache.set('us:{}'.format(self.session_token), self.id)
        login_user(self)

    def logout(self):
        cache.delete('us:{}'.format(self.session_token))
        logout_user()

    def register(self):
        # save self
        self.save()

        # create and send verification
        verification = EmailVerification(self)
        verification.create()

        # maybe some more setups for new user

    def change_email(self, email):
        """
        Change users email under lock and send email for re-verification of his email
        :param email:
        """
        with self.get_read_modify_write_lock():
            # change email
            self.email = email
            self.email_verified = False

            # update
            self.save()

            # send verification
            verification = EmailVerification(self)
            verification.create()

    @staticmethod
    @login_manager.user_loader
    def load_user(session_id):
        uid = cache.get('us:{}'.format(session_id))

        u = User.by_id(uid)
        if u is not None:
            u._accessor_cache["session_token"] = session_id
        return u

    @classmethod
    def by_id(cls, id):
        u = cls.load_from_cache(id)
        if u is not None:
            return u
        u = User.where('id', id).first()
        if u is not None:
            u.write_to_cache()
        return u

    def update_with_cache(self):
        self.save()
        self.write_to_cache()

    @classmethod
    def _cache_prefix(cls):
        return "u:"

    @property
    def age(self):
        return self.created_at - datetime.utcnow()

    @belongs_to_many('feeds_users')
    def feeds(self):
        from news.models.feed import Feed
        return Feed

    @has_many
    def links(self):
        from news.models.link import Link
        return Link

    @has_many
    def comments(self):
        from news.models.comment import Comment
        return Comment

    @cache.memoize()
    def subscribed_feed_ids(self):
        return [feed.id for feed in self.feeds]

    @accessor
    def subscribed_feeds(self):
        from news.models.feed import Feed
        return [Feed.by_id(x) for x in self.subscribed_feed_ids()]

    def subscribed_to(self, feed):
        return feed.id in self.subscribed_feed_ids()

    def subscribe(self, feed):
        if self.feed_subs >= MAX_SUBSCRIPTIONS_FREE:
            return False

        self.feeds().attach(feed)
        self.incr('feed_subs', 1)

        # TODO add to subscribed feed ids
        cache.delete_memoized(self.subscribed_feed_ids)
        return True

    def unsubscribe(self, feed):
        self.feeds().detach(feed.id)
        self.decr('feed_subs', 1)

        # TODO add to subscribed feed ids
        cache.delete_memoized(self.subscribed_feed_ids)
        return True

    @classmethod
    def by_username(cls, username):
        return User.where('username', username).first()

    def is_god(self):
        if not self.is_authenticated:
            return False
        return self.username in GODS

    def is_feed_admin(self, feed):
        if not self.is_authenticated:
            return False
        return FeedAdmin.by_user_and_feed_id(self.id, feed.id) is not None

    def is_feed_god(self, feed):
        if not self.is_authenticated:
            return False
        feed_admin = FeedAdmin.by_user_and_feed_id(self.id, feed.id)
        return feed_admin.god if feed_admin is not None else False


class SignUpForm(Form):
    username = StringField('Username', [DataRequired(), Length(min=3,max=20)], render_kw={'placeholder': 'Username'})
    email = EmailField('Email', [DataRequired()], render_kw={'placeholder': 'Email'})
    password = PasswordField('Password', [DataRequired(), Length(min=6)], render_kw={'placeholder': 'Password', 'autocomplete': "new-password"})

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
    username_or_email = StringField('Username or email', [DataRequired()], render_kw={'placeholder': 'Username or email'})
    password = PasswordField('Password', [DataRequired()], render_kw={'placeholder': 'Password'})

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
        if not self.user.check_password(self.password.data):
            self.errors['general'] = "Invalid username or password"
            return False
        return True


class PreferencesForm(Form):
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


class PasswordForm(Form):
    new_password = PasswordField('New password', [Length(min=6)], render_kw={'autocomplete': "new-password"})
    new_password_again = PasswordField('New password again', render_kw={'autocomplete': "new-password"})
    old_password = PasswordField('Old password', render_kw={'autocomplete': 'off'})

    def __init__(self, user, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = user

    def validate(self):
        if not self.user.check_password(self.old_password.data):
            print("wrong pw")
            self.errors['password'] = 'Invalid password'
            return False
        if not self.new_password.data == self.new_password_again.data:
            self.errors['passwords'] = 'Passwords don\'t match'
            return False
        return True


class EmailForm(Form):
    email = EmailField('Email')

    def __init__(self, user, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = user
        self.email.data = user.email

    def validate(self):
        if self.email.data == self.user.email:
            return False
        return True


class DeactivateForm(Form):
    pass


class ProfileForm(Form):
    full_name = StringField('Full name', )
    bio = TextAreaField('Bio', [Length(max=8192)], render_kw={'rows': 6, 'autocomplete': 'off'})
    url = URLField(validators=[URL()])

    def validate(self):
        return True

class ResetForm(Form):
    email = EmailField('Email', [DataRequired()])

    def validate(self):
        return True

class SetPasswordForm(Form):
    password = PasswordField('Password', [DataRequired(), Length(min=6)], render_kw={'placeholder': 'New password'})
    password_again = PasswordField('Password again', [DataRequired()], render_kw={'placeholder': 'New password again'})
    user_id = HiddenField('username')

    def validate(self):
        return self.password.data == self.password_again.data


PASSWORD_RESET_EXPIRE = 60*60* 1  # 48 hours


class PasswordReset:
    """
    Email Verification handles email verifications
    """

    def __init__(self, user=None, token=''):
        self.user = user
        self.token = token

    def verify(self):
        """
        Checks if given verification exists
        :return:
        """
        return redis_conn.get(self._cache_key) is not None

    @property
    def user_id(self):
        """
        Returns ID of user for whom this verification applies
        :return: user ID
        """
        return int(redis_conn.get(self._cache_key))

    @property
    def _cache_key(self):
        """
        Cache key for email verification
        :return: cache key
        """
        return 'p_reset:{}'.format(self.token)

    @property
    def _url(self):
        """
        Formatted URL with verification link
        :return:
        """
        return "localhost:5000/reset_password?t={}".format(self.token)

    def create(self):
        """
        Creates email verification which expires after given time
        and sends email to user to verify his email
        """

        # create token
        self.token = token_urlsafe(16)

        # save token to redis for limited time
        pipe = redis_conn.pipeline()
        pipe.set(self._cache_key, self.user.id)
        pipe.expire(self._cache_key, PASSWORD_RESET_EXPIRE)
        pipe.execute()

        # send email with verification link
        msg = reset_email(self.user, self._url)
        q.enqueue(send_mail, msg, result_ttl=0)
