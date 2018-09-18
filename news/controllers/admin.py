from flask import render_template
from flask_login import current_user
from werkzeug.utils import redirect

from news.lib.cache import cache
from news.lib.task_queue import q
from news.lib.tasks.tasks import JOB_import_feed_fqs
from news.models.feed import Feed


def admin():
    if not current_user.is_authenticated:
        return redirect('/login')

    if not current_user.is_god:
        return redirect('/')

    all_feeds = Feed.get()
    return render_template('admin.html', all_feeds=all_feeds)


def add_testing_data():
    from news.scripts.create_testing_data import create_stories
    create_stories()

    return redirect('/admin')


def archive_old_links():
    from news.scripts.archive_links import archive_links
    archive_links()

    return redirect('/admin')


def trigget_update_fqs():
    from news.scripts.import_fqs import import_fqs
    import_fqs()

    return redirect('/admin')


def clear_cache():
    cache.clear()
    return redirect('/admin')


def trigger_fqs_update():
    q.enqueue(JOB_import_feed_fqs, ttl=0)
    return redirect('/admin')
