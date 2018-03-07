import bcrypt
from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from news.lib.cache import cache
from news.lib.login import login_manager
from news.lib.db.db import db, schema


class User(db.Model):
    __table__ = 'users'
    __fillable__ = ['username', 'full_name', 'email', 'email_verified', 'subscribed']
    __guarded__ = ['id', 'password','reported','spammer']

    @classmethod
    def create_table(cls):
        schema.drop_if_exists('users')
        with schema.create('users') as table:
            table.big_increments('id')
            table.char('username', 32).unique()
            table.char('full_name', 64).nullable()
            table.char('email', 128).unique()
            table.boolean('email_verified').default(False)
            table.boolean('subscribed').default(False)
            table.char('password', 128)
            table.boolean('reported').default(False)
            table.boolean('spammer').default(False)
            table.datetime('created_at')
            table.datetime('updated_at')
            table.index('username')
            table.index('email')

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __repr__(self):
        return '<User %r>' % self.username

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def get_id(self):
        return self.username

    @classmethod
    @cache.memoize()
    def by_name(cls, name):
        return User.where('username', name).first()

    @staticmethod
    @login_manager.user_loader
    def load_user(session_id):
        return User.by_name(session_id)

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, password):
        return bcrypt.checkpw(password, self.password)

    @classmethod
    def _cache_prefix(cls):
        return "u:"

    def name(self):
        if self.full_name is not None:
            return self.full_name
        return self.username


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
