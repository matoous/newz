from datetime import datetime
from secrets import token_urlsafe
from typing import Optional, List

from flask import current_app
from flask_login import current_user, login_user, logout_user
from flask_wtf import FlaskForm
from orator import accessor, Schema
from passlib.hash import bcrypt
from rq.decorators import job
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField, HiddenField, BooleanField, \
    FileField
from wtforms.fields.html5 import EmailField, URLField
from wtforms.validators import DataRequired, URL, Length

from news.lib.cache import cache
from news.lib.db.db import db
from news.lib.login import login_manager
from news.lib.mail import reset_email, send_mail
from news.lib.task_queue import q, redis_conn
from news.lib.validators import UniqueUsername, UniqueEmail
from news.lib.verifications import EmailVerification
from news.models.ban import Ban
from news.models.base import Base
from news.models.disposable_token import DisposableToken
from news.models.feed_admin import FeedAdmin

MAX_SUBSCRIPTIONS_FREE = 50


class User(Base):
    __table__ = 'users'
    __fillable__ = ['id', 'password', 'reported', 'spammer', 'username', 'full_name', 'email', 'email_verified',
                    'subscribed', 'preferred_sort', 'bio', 'url', 'profile_pic', 'email_public', 'feed_subs',
                    'p_infinite_scrolling', 'p_show_summaries', 'p_min_link_score']
    __hidden__ = ['password', 'feeds', 'links', 'comments', 'age', 'ld', 'lu', 'cd', 'cu']
    __append__ = ['session_token']

    @classmethod
    def create_table(cls, database):
        schema = Schema(database)
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
        """
        Get users name
        Full name if available, username otherwise
        :return: users name
        """
        return self.full_name or self.username

    def set_password(self, password: str):
        """
        Set users password
        :param password: new password
        """
        self.set_attribute('password', bcrypt.hash(password))

    def check_password(self, password: str) -> bool:
        """
        Check users password
        :param password: submitted password
        :return:
        """
        return bcrypt.verify(password, self.password)

    def get_id(self) -> str:
        return self.session_token or ''

    @accessor
    def session_token(self) -> str:
        return self._accessor_cache['session_token']

    def login(self, remember_me: bool = False):
        """
        Login the user
        Generate access token which gets saved in session, info about user is then saved to redis
        :param remember_me:
        """
        token = DisposableToken.get()
        self._accessor_cache['session_token'] = token.id
        session_key = 'us:{}'.format(self.session_token)
        cache.set(session_key, self.id, ttl=0 if remember_me else 60 * 60 * 2, raw=True)
        login_user(self, remember=remember_me)

        # Ip.from_request()

    def logout(self):
        """
        Logout the user
        """
        cache.delete('us:{}'.format(self.session_token))
        logout_user()

    def register(self):
        """
        Register new user and send email verification
        """
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
            self.update_with_cache()

        # send verification
        verification = EmailVerification(self)
        verification.create()

    @staticmethod
    @login_manager.user_loader
    def load_user(session_id: str) -> Optional['User']:
        """
        Load user by session id

        Loads the user by session id from cache

        :param session_id: session id
        :return: maybe user
        """
        user_id = cache.get('us:{}'.format(session_id), raw=True)

        if not user_id:
            return None

        uid = int(user_id)

        u = User.by_id(uid)
        if u is not None:
            u._accessor_cache["session_token"] = session_id
        return u

    @classmethod
    def by_id(cls, id: int) -> Optional['User']:
        """
        Get user by id
        :param id:
        :return:
        """
        u = cls.load_from_cache(id)
        if u is not None:
            return u
        u = User.where('id', id).first()
        if u is not None:
            u.write_to_cache()
        return u

    @classmethod
    def _cache_prefix(cls) -> str:
        return "u:"

    @property
    def age(self) -> datetime:
        """
        Users eSource news age
        :return: age
        """
        return datetime.utcnow() - self.created_at

    @property
    def links(self):
        """
        Users posted links
        :return: links
        """
        from news.models.link import Link
        return Link.where('user_id', self.id).get()

    @property
    def comments(self):
        """
        Users posted comments
        :return: comments
        """
        from news.models.comment import Comment
        return Comment.where('user_id', self.id).get()

    @property
    def feeds(self):
        """
        Users subscribed feeds
        :return: feeds
        """
        return db.table('feeds').join('feeds_users', 'feeds.id', '=', 'feeds_users.feed_id').where(
            'feeds_users.user_id', self.id).get()

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
    def subscribed_feeds(self) -> List['Feed']:
        from news.models.feed import Feed
        return [Feed.by_id(x) for x in self.subscribed_feed_ids]

    def subscribed_to(self, feed: 'Feed') -> bool:
        """
        Check if user is subscribed to given feed
        :param feed: feed
        :return: is user subscribed to the feed
        """
        return feed.id in self.subscribed_feed_ids

    def subscribe(self, feed: 'Feed'):
        """
        Subscribe user to given feed
        :param feed: feed to subscribe
        :return:
        """
        if self.feed_subs >= MAX_SUBSCRIPTIONS_FREE:
            return False

        # if user is banned from feed he can't subscribe
        if Ban.by_user_and_feed(self, feed) is not None:
            return False

        # save subscription
        db.table('feeds_users').insert(user_id=self.id, feed_id=feed.id)
        key = 'subs:{}'.format(self.id)
        ids = cache.get(key) or []
        ids.append(feed.id)
        cache.set(key, ids)

        self.incr('feed_subs', 1)
        self.update_with_cache()

        # TODO DO IN QUEUE
        feed.incr('subscribers_count', 1)
        return True

    def unsubscribe(self, feed: 'Feed'):
        db.table('feeds_users').where('user_id', '=', self.id).where('feed_id', '=', feed.id).delete()
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
        in_cache = cache.get(cache_key, raw=True)
        uid = int(in_cache) if in_cache else None

        # return user on success
        if uid is not None:
            return User.by_id(uid)

        # try to load user from DB on failure
        u = User.where('username', username).first()

        # cache the result
        if u is not None:
            cache.set(cache_key, u.id, raw=True)
            u.write_to_cache()

        return u

    def is_god(self) -> bool:
        return self.is_authenticated and self.username in current_app.config['GODS']

    def is_feed_admin(self, feed: 'Feed') -> bool:
        if not self.is_authenticated:
            return False
        return FeedAdmin.by_user_and_feed_id(self.id, feed.id) is not None

    def is_feed_god(self, feed: 'Feed') -> bool:
        if not self.is_authenticated:
            return False
        feed_admin = FeedAdmin.by_user_and_feed_id(self.id, feed.id)
        return feed_admin.god if feed_admin is not None else False

    def is_baned_from(self, feed: 'Feed') -> bool:
        return Ban.by_user_and_feed(self, feed) is not None

    @property
    def route(self) -> str:
        return "/u/{}".format(self.username)

    @property
    def link_upvotes(self):
        from news.models.vote import LinkVote
        if 'lu' not in self._relations:
            self._relations['lu'] = LinkVote.upvotes_by_user(self)
        return self._relations['lu']

    @property
    def link_downvotes(self):
        from news.models.vote import LinkVote
        if 'ld' not in self._relations:
            self._relations['ld'] = LinkVote.downvotes_by_user(self)
        return self._relations['ld']

    @property
    def comment_upvotes(self):
        from news.models.vote import LinkVote
        if 'cu' not in self._relations:
            self._relations['cu'] = LinkVote.upvotes_by_user(self)
        return self._relations['cu']

    @property
    def comment_downvotes(self):
        from news.models.vote import LinkVote
        if 'cd' not in self._relations:
            self._relations['cd'] = LinkVote.downvotes_by_user(self)
        return self._relations['cd']


class SignUpForm(FlaskForm):
    username = StringField('Username',
                           [DataRequired(message='You have to select username'),
                            Length(min=3, max=20, message='Username must be between 3 and 20 characters long'),
                            UniqueUsername(message='This username is already taken')],
                           render_kw={'placeholder': 'Username'})
    email = EmailField('Email',
                       [DataRequired('You have to enter your email'),
                        UniqueEmail()],
                       render_kw={'placeholder': 'Email'})
    password = PasswordField('Password',
                             [DataRequired('You have to choose password'),
                              Length(min=6, message='Password must be at least 6 characters long')],
                             render_kw={'placeholder': 'Password', 'autocomplete': "new-password"})

    def result(self):
        user = User(username=self.username.data, email=self.email.data)
        user.set_password(self.password.data)
        return user


class LoginForm(FlaskForm):
    username_or_email = StringField('Username or email',
                                    [DataRequired(message='Enter you email or username')],
                                    render_kw={'placeholder': 'Username or email'})
    password = PasswordField('Password',
                             [DataRequired(message='Incorrect username or password')],
                             render_kw={'placeholder': 'Password'})
    remember_me = BooleanField('Remember me')

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            self.errors['general'] = 'Invalid username or password'
            return False

        # try to find user, from DB explicitly
        if '@' in self.username_or_email.data:
            self._user = User.where('email', self.username_or_email.data).first()
        else:
            self._user = User.where('username', self.username_or_email.data).first()

        # no user found
        if self._user is None:
            self.errors['general'] = 'Invalid username or password'
            return False

        # wrong password
        if not self._user.check_password(self.password.data):
            self.errors['general'] = 'Invalid username or password'
            return False

        return True

    def user(self):
        return self._user


class PreferencesForm(FlaskForm):
    subscribe = BooleanField('Subscribe to newsletter')
    min_link_score = IntegerField('Minimal link score')
    infinite_scrolling = BooleanField('Load new links upon reaching bottom of the feed')
    show_summaries = BooleanField('Show link summaries')
    #send_digest = BooleanField('Subscribe to best articles of week')
    #show_images = SelectField('Show Images', choices=[('y', 'Always'), ('m', 'Homepage only'), ('n', 'Never')])

    def fill(self, user):
        self.subscribe.data = user.subscribed
        self.min_link_score.data = user.p_min_link_score
        self.infinite_scrolling.data = user.p_infinite_scrolling
        self.show_summaries.data = user.p_show_summaries


class PasswordForm(FlaskForm):
    new_password = PasswordField('New password',
                                 [DataRequired('You have to choose password'),
                                  Length(min=6, message='Password must be at least 6 characters long')],
                                 render_kw={'placeholder': 'New password', 'autocomplete': "new-password"})
    new_password_again = PasswordField('New password again',
                                       [DataRequired('You have to choose password'),
                                        Length(min=6, message='Password must be at least 6 characters long')],
                                       render_kw={'placeholder': 'Password', 'autocomplete': "new-password"})
    old_password = PasswordField('Old password', render_kw={'autocomplete': 'off'})

    def validate(self):
        if not current_user.is_authenticated:
            return False

        user = User.by_id_slow(current_user.id)
        if not user.check_password(self.old_password.data):
            self.errors['password'] = 'Invalid password'
            return False

        if not self.new_password.data == self.new_password_again.data:
            self.errors['passwords'] = 'Passwords don\'t match'
            return False

        return True


class EmailForm(FlaskForm):
    email = EmailField('Email', [DataRequired(), UniqueEmail()])
    public = BooleanField('Email public')

    def fill(self, user):
        self.email.data = user.email
        self.public.data = user.email_public


class DeactivateForm(FlaskForm):
    username = StringField('Your username', [], render_kw={'autocomplete': 'off', 'placeholder': 'Your username'})
    password = PasswordField('Your password', [], render_kw={'placeholder': 'Your password'})

    def validate(self, u):
        user = User.by_id_slow(current_user.id)
        if user.username != self.username.data:
            return False
        if not user.check_password(self.password.data):
            return False
        return True


class ProfileForm(FlaskForm):
    full_name = StringField('Full name', )
    bio = TextAreaField('Bio', [Length(max=8192)], render_kw={'rows': 6, 'autocomplete': 'off'})
    url = URLField(validators=[URL()])
    img = FileField('Avatar')

    def validate(self):
        return True


class ResetForm(FlaskForm):
    email = EmailField('Email', [DataRequired()], render_kw={'placeholder': 'Email'})

    def validate(self):
        return True


class SetPasswordForm(FlaskForm):
    password = PasswordField('Password', [DataRequired(), Length(min=6)], render_kw={'placeholder': 'New password'})
    password_again = PasswordField('Password again', [DataRequired()], render_kw={'placeholder': 'New password again'})
    user_id = HiddenField('username')

    def validate(self):
        return self.password.data == self.password_again.data


PASSWORD_RESET_EXPIRE = 60 * 60 * 1  # 48 hours


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
        return cache.get(self._cache_key, raw=True) is not None

    @property
    def user_id(self):
        """
        Returns ID of user for whom this verification applies
        :return: user ID
        """
        return int(cache.get(self._cache_key, raw=True))

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
        return "{}/reset_password/{}".format(current_app.config['URL'], self.token)

    def create(self):
        """
        Creates email verification which expires after given time
        and sends email to user to verify his email
        """

        # create token
        self.token = token_urlsafe(16)

        # save token to redis for limited time
        cache.set(self._cache_key, self.user.id, ttl=PASSWORD_RESET_EXPIRE, raw=True)

        # send email with verification link
        msg = reset_email(self.user, self._url)
        q.enqueue(send_mail, msg, result_ttl=0)

    def delete(self):
        cache.delete(self._cache_key)


@job('medium', connection=redis_conn)
def make_new_avatar(file_name):
    pass
