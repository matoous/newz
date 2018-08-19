from wtforms import ValidationError


class UniqueUsername(object):
    """
    Check that given string is unique username
    """

    def __init__(self, message=None):
        if not message:
            message = 'This username is already taken'
        self.message = message

    def __call__(self, form, field):
        username = field.data
        from news.models.user import User
        if User.by_username(username) is not None:
            raise ValidationError(self.message)


class UniqueEmail(object):
    """
    Check that given string is unique email
    """
    def __init__(self, message=None):
        if not message:
            message = 'This email is already taken'
        self.message = message

    def __call__(self, form, field):
        email = field.data
        from news.models.user import User
        if User.where('email', email).first() is not None:
            raise ValidationError(self.message)