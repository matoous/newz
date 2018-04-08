from flask import Blueprint, request, redirect

search_blueprint = Blueprint('search', __name__, template_folder='/templates')


@search_blueprint.route('/search')
def search():
    q = request.args.get('q')
    print(q)
    return redirect("/")

