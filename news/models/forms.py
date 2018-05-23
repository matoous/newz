from flask_wtf import Form
from wtforms import TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length


class ContactUsForm(Form):
    email = EmailField('Title', [DataRequired()], render_kw={'placeholder': 'Email', 'autocomplete': 'off'})
    text = TextAreaField('Text', [Length(max=8192)], render_kw={'placeholder': 'Message', 'rows': 6, 'autocomplete': 'off'})

    def validate(self):
        return True