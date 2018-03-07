from flask import Blueprint
from flask_login import login_required

web = Blueprint('web', __name__, template_folder='/templates')


@web.route('/')
def home():
    return 'Hello World! Home'


@web.route('/hello')
@login_required
def hello_world():
    return 'Hello World!'
