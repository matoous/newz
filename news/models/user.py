from datetime import datetime
from secrets import token_urlsafe
from typing import Optional, List

from flask_login import current_user, login_user, logout_user
from flask_wtf import Form
from orator import accessor
from orator.orm import belongs_to_many, has_many
from passlib.hash import bcrypt
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField, HiddenField, BooleanField
from wtforms.fields.html5 import EmailField, URLField
from wtforms.validators import DataRequired, URL, Length

from news.config.config import GODS
from news.lib.app import app
from news.lib.cache import cache, conn
from news.lib.db.db import schema
from news.lib.login import login_manager
from news.lib.mail import reset_email, send_mail
from news.lib.queue import redis_conn, q
from news.lib.verifications import EmailVerification
from news.models.ban import Ban
from news.models.base import Base, CACHE_EXPIRE_TIME
from news.models.feed_admin import FeedAdmin
from news.models.token import DisposableToken

MAX_SUBSCRIPTIONS_FREE = 50


class User(Base):
    __table__ = 'users'
    __fillable__ = ['id', 'password', 'reported', 'spammer', 'username', 'full_name', 'email', 'email_verified', 'subscribed', 'preferred_sort', 'bio', 'url',
                    'profile_pic', 'email_public', 'feed_subs',
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

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.id == other.id

    @property
    def is_active(self) -> bool:
        return True

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def name(self) -> str:
        return self.full_name if self.full_name is not None else self.username

    def set_password(self, password: str):
        self.set_attribute('password', bcrypt.hash(password))

    def check_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password)

    def get_id(self) -> str:
        return self.session_token or ''

    @accessor
    def session_token(self):
        return self._accessor_cache['session_token']

    def login(self, remember_me: bool = False):
        token = DisposableToken.get()
        self._accessor_cache['session_token'] = token.id
        session_key = 'us:{}'.format(self.session_token)
        # TODO maybe expire the session key after some time?
        conn.set(session_key, self.id)
        login_user(self, remember=remember_me)

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
        # TODO subscribe to some default feeds

    def change_email(self, email: str):
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
            self.write_to_cache()

        # send verification
        verification = EmailVerification(self)
        verification.create()

    @staticmethod
    @login_manager.user_loader
    def load_user(session_id: str) -> Optional['User']:
        uid = int(conn.get('us:{}'.format(session_id)))

        u = User.by_id(uid)
        if u is not None:
            u._accessor_cache["session_token"] = session_id
        return u

    @classmethod
    def by_id(cls, id: int) -> Optional['User']:
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
    def age(self) -> datetime:
        return datetime.utcnow() - self.created_at

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

    @accessor
    def subscribed_feed_ids(self) -> List[str]:
        """
        Get users subscribed feed ids
        :return: list of ids
        """
        key = 'subs:{}'.format(self.id)
        ids = cache.get(key)
        if ids is None:
            ids = [feed.id for feed in self.feeds]
            cache.set(key, ids)
        return ids

    @accessor
    def subscribed_feeds(self) -> List[object]:
        from news.models.feed import Feed
        return [Feed.by_id(x) for x in self.subscribed_feed_ids]

    def subscribed_to(self, feed: object) -> bool:
        """
        Check if user is subscribed to given feed
        :param feed: feed
        :return: is user subscribed to the feed
        """
        return feed.id in self.subscribed_feed_ids

    def subscribe(self, feed):
        """
        Subscribe user to given feed
        TODO allow users to by 'pro' and have more than max subscriptions
        :param feed: feed to subscribe
        :return:
        """
        if self.feed_subs >= MAX_SUBSCRIPTIONS_FREE:
            return False

        if Ban.by_user_and_feed(self, feed) is not None:
            return False

        self.feeds().attach(feed)
        self.incr('feed_subs', 1)

        # TODO DO IN QUEUE
        feed.incr('subscribers_count', 1)
        key = 'subs:{}'.format(self.id)
        ids = cache.get(key) or []
        ids.append(feed.id)
        cache.set(key, ids)
        return True

    def unsubscribe(self, feed):
        self.feeds().detach(feed.id)
        self.decr('feed_subs', 1)

        # TODO DO IN QUEUE
        feed.decr('subscribers_count', 1)
        key = 'subs:{}'.format(self.id)
        ids = cache.get(key)
        if ids is not None:
            ids = [id for id in ids if id != feed.id]
            cache.set(key, ids)
        return True

    @classmethod
    def by_username(cls, username: str) -> Optional['User']:
        """
        Get user by username
        :param username: username
        :return:
        """
        cache_key = 'uname:{}'.format(username)

        # check username cache
        in_cache = conn.get(cache_key)
        uid = int(in_cache) if in_cache else None

        # return user on success
        if uid is not None:
            return User.by_id(uid)

        # try to load user from DB on failure
        u = User.where('username', username).first()

        # cache the result
        if u is not None:
            conn.set(cache_key, u.id)
            conn.expire(cache_key, CACHE_EXPIRE_TIME)
            u.write_to_cache()

        return u

    def is_god(self) -> bool:
        if not self.is_authenticated:
            return False
        return self.username in GODS

    def is_feed_admin(self, feed: object) -> bool:
        if not self.is_authenticated:
            return False
        return FeedAdmin.by_user_and_feed_id(self.id, feed.id) is not None

    def is_feed_god(self, feed):
        if not self.is_authenticated:
            return False
        feed_admin = FeedAdmin.by_user_and_feed_id(self.id, feed.id)
        return feed_admin.god if feed_admin is not None else False

    def is_baned_from(self, feed):
        return Ban.by_user_and_feed(self, feed) is not None

    @property
    def route(self):
        return "/u/{}".format(self.username)

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
    remember_me = BooleanField('Remember me')

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
    subscribe = BooleanField('Subscribe to newsletter')
    send_digest = BooleanField('Subscribe to best articles of week')
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
    public = BooleanField('Email public')

    def __init__(self, user, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = user
        self.email.data = user.email
        self.public.data = user.email_public

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
    email = EmailField('Email', [DataRequired()], render_kw={'placeholder': 'Email'})

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
        return "{}/reset_password/{}".format(app.config['ME'], self.token)

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
