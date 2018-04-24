from flask import Blueprint, redirect, render_template, Response, request, abort
from flask_login import login_required, current_user
from feedgen.feed import FeedGenerator

from news.lib.access import feed_admin_required
from news.lib.db.query import LinkQuery
from news.lib.filters import min_score_filter
from news.lib.pagination import paginate
from news.models.comment import CommentForm, SortedComments, Comment
from news.models.feed import FeedForm, Feed
from news.models.feed_admin import FeedAdmin
from news.models.link import LinkForm, Link
from news.models.user import User
from news.models.vote import LinkVote, vote_type_from_string, CommentVote

feed_blueprint = Blueprint('feed', __name__, template_folder='/templates')


@feed_blueprint.route("/new_feed", methods=['GET', 'POST'])
@login_required
def new_feed():
    form = FeedForm()
    if request.method == 'POST' and form.validate():
        feed = form.feed
        feed.commit()
        return redirect('/f/{feed}'.format(feed=feed.slug))
    return render_template("new_feed.html", form=form)


@feed_blueprint.route('/f/<feed:feed>')
@feed_blueprint.route('/f/<feed:feed>/<any(trending, new, best):sort>')
def get_feed(feed, sort=None):
    if (sort is None or sort not in ['trending', 'new', 'best']) and current_user.is_authenticated:
        sort = current_user.preferred_sort
    if sort is None:
        sort = feed.default_sort

    lids, has_less, has_more = paginate(LinkQuery(feed_id=feed.id, sort=sort).fetch_ids(), 20)
    links = [Link.by_id(link_id) for link_id in lids]

    if sort == 'new':
        links = filter(min_score_filter(current_user.p_min_link_score), links)

    feed.links = links
    return render_template("feed.html",
                           feed=feed,
                           less_links=has_less,
                           more_links=has_more,
                           sort=sort)

@feed_blueprint.route('/f/<feed:feed>/rss')
def get_feed_rss(feed):
    lids, has_less, has_more = paginate(LinkQuery(feed_id=feed.id, sort='trending').fetch_ids(), 30)
    links = [Link.by_id(link_id) for link_id in lids]
    fg = FeedGenerator()
    fg.id(feed.url)
    fg.title(feed.name)
    fg.link(href="http://localhost:5000" + feed.url, rel='self')
    fg.description(feed.description or "Hello, there is some description.")
    fg.language(feed.lang)
    for link in links:
        fe = fg.add_entry()
        fe.title(link.title)
        # TODO if is self post put in content, else summary
        fe.content(link.text)
        fe.summary(link.text)
        fe.link(href='http://localhost:5000' + link.url)
        # TODO hide email if user wants to
        fe.author(name=link.user.name, email=link.user.email)

    return fg.rss_str(pretty=True)


@feed_blueprint.route("/f/<feed:feed>/add", methods=['POST', 'GET'])
@login_required
def add_link(feed):
    form = LinkForm()
    if request.method == 'POST':
        if form.validate(feed, current_user):
            link = form.link
            link.commit()

            return redirect('/f/{feed}'.format(feed=feed.slug))

    return render_template("new_link.html", form=form, feed=feed, md_parser=True)


@feed_blueprint.route("/l/<link>/vote/<vote_str>")
@login_required
def do_vote(link=None, vote_str=None):
    link = Link.where('slug', link).first()
    vote = vote_type_from_string(vote_str)
    if link is None or vote is None:
        abort(404)

    vote = LinkVote(user_id=current_user.id, link_id=link.id, vote_type=vote)
    print(vote.__dict__)
    vote.apply()

    return "voted"


@feed_blueprint.route("/f/<feed:feed>/subscribe")
@login_required
def subscribe(feed):
    subscribed = current_user.subscribe(feed)
    if not subscribed:
        return "Subscribe NOT OK"
    return "Subscribed"


@feed_blueprint.route("/f/<feed:feed>/unsubscribe")
@login_required
def unsubscribe(feed):
    current_user.unsubscribe(feed)
    return "Unsubscribed"


@feed_blueprint.route("/f/<feed:feed>/<link_slug>")
def link_view(feed, link_slug=None):
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    comment_form = CommentForm()

    sorted_comments = SortedComments(link).get_full_tree()
    return render_template('link.html', link=link, feed=feed, comment_form=comment_form, comments=sorted_comments,
                           get_comment=Comment.by_id)


@login_required
@feed_blueprint.route("/f/<feed:feed>/<link_slug>/comment", methods=['POST'])
def comment_link(feed, link_slug=None):
    link = Link.where('slug', link_slug).first()
    if link is None:
        abort(404)

    comment_form = CommentForm()
    if comment_form.validate(current_user, link):
        comment = comment_form.comment
        comment.commit()
    return redirect('/f/{}/{}'.format(feed.slug, link_slug))


@feed_blueprint.route("/c/<comment_id>/vote/<vote_str>")
@login_required
def do_comment_vote(comment_id=None, vote_str=None):
    comment = Comment.by_id(comment_id)
    vote = vote_type_from_string(vote_str)
    if comment is None or vote is None:
        abort(404)

    vote = CommentVote(user_id=current_user.id, comment_id=comment.id, vote_type=vote)
    vote.apply()

    return "voted"


@feed_blueprint.route("/f/<feed:feed>/add_admin", methods=['POST'])
@feed_admin_required
def do_add_admin(feed):
    #get new admin username
    username = request.form.get('username')
    if not username or username == "":
        abort(404)

    # check privileges
    if current_user.is_god() or current_user.is_feed_god(feed):
        user = User.by_username(username)
        if user is None:
            abort(404)
        feed_admin = FeedAdmin.create(user_id=user.id,
                                      feed_id=feed.id)
        return redirect("/f/{}/admins".format(feed.slug))
    else:
        abort(403)


@feed_blueprint.route("/f/<feed:feed>/admins/")
@feed_admin_required
def get_feed_admins(feed):
    admins = FeedAdmin.by_feed_id(feed.id)
    return render_template("feed_admins.html", admins=admins, feed=feed)


@feed_blueprint.route("/f/<feed:feed>/admin")
@feed_admin_required
def get_feed_admin(feed):
    form = FeedForm()
    form.fill(feed)
    return render_template("feed_admin.html", feed=feed, form=form)


@feed_blueprint.route("/f/<feed:feed>/admin", methods=['POST'])
@feed_admin_required
def post_feed_admin(feed):
    form = FeedForm()
    if form.validate():
        feed.name = form.name.data
        feed.description = form.description.data
        feed.rules = form.rules.data
        feed.update()
        feed.write_to_cache()
        return redirect('/f/{}/admin'.format(feed.slug))
    return render_template("feed_admin.html", feed=feed, form=form)


@feed_blueprint.route("/f/<feed:feed>/bans")
@feed_admin_required
def get_feed_bans(feed):
    return render_template("feed_bans.html", feed=feed)

@feed_blueprint.route("/f/<feed:feed>/ban", methods=['POST'])
@feed_admin_required
def ban_user(feed):
    pass