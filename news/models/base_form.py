from flask_wtf import FlaskForm


class BaseForm(FlaskForm):
    def fill(self, thing):
        """
        Fill the form
        :param thing:
        """
        raise NotImplemented

    def result(self) -> object:
        """
        Get result of the form
        """
        raise NotImplemented
