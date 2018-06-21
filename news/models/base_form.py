from flask_wtf import Form


class BaseForm(Form):
    def fill(self, thing):
        raise NotImplemented

    def result(self):
        raise NotImplemented