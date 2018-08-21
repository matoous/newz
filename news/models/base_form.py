from flask_wtf import FlaskForm


class BaseForm(FlaskForm):
    def fill(self, thing):
        raise NotImplemented

    def result(self):
        raise NotImplemented
