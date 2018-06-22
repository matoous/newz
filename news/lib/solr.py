import pysolr as pysolr
from rq.decorators import job

from news.lib.app import app
from news.lib.task_queue import redis_conn

linksolr = pysolr.Solr(app.config['SOLR_URL'] + '/links', timeout=10)
usersolr = pysolr.Solr(app.config['SOLR_URL'] + '/users', timeout=10)
feedsolr = pysolr.Solr(app.config['SOLR_URL'] + '/feeds', timeout=10)


@job('medium', connection=redis_conn)
def new_link_queue(link):
    app.logger.info('Adding new link to solr: {}'.format(link.title))
    linksolr.add([link.to_solr()])
    return None

@job('medium', connection=redis_conn)
def new_user_queue(user):
    app.logger.info('Adding new user to solr: {}'.format(user.username))
    usersolr.add([user.to_solr()])
    return None

def add_feed_to_search(feed):
    app.logger.info('Adding new feed to solr: {}'.format(feed.name))
    feedsolr.add([feed.to_solr()])
    return None
