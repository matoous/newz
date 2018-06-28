import pysolr as pysolr
from rq.decorators import job

from news.lib.task_queue import redis_conn

class Solr:
    def __init__(self, app=None):
        self._config = None
        self.linksolr = None
        self.usersolr = None
        self.feedsolr = None
        self.logger = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if 'REDIS' not in app.config:
            raise RuntimeError('Missing "REDIS" configuration')

        self._config = app.config['SOLR']

        self.linksolr = pysolr.Solr(self._config['URL'] + '/links', timeout=10)
        self.usersolr = pysolr.Solr(self._config['URL'] + '/users', timeout=10)
        self.feedsolr = pysolr.Solr(self._config['URL'] + '/feeds', timeout=10)

        self.logger = app.logger

    def search_links(self, q, options=None):
        if options is None:
            options = {
                'hl.fl': '*',
                'hl': 'on',
                'hl.snippets': 1,
                'hl.fragsize': 0,
            }
        return self.linksolr.search('text:{} title:{}'.format(q, q), options)

    def search_feeds(self, q, options=None):
        if options is None:
            options = {
                'hl.fl': '*',
                'hl': 'on',
                'hl.snippets': 1,
                'hl.fragsize': 0,
            }
        return self.feedsolr.search('name:{} description:{}'.format(q, q), options)

solr = Solr()

@job('medium', connection=redis_conn)
def new_link_queue(link):
    solr.logger.info('Adding new link to solr: {}'.format(link.title))
    solr.linksolr.add([link.to_solr()])
    return None

@job('medium', connection=redis_conn)
def new_user_queue(user):
    solr.logger.info('Adding new user to solr: {}'.format(user.username))
    solr.usersolr.add([user.to_solr()])
    return None

def add_feed_to_search(feed):
    solr.logger.info('Adding new feed to solr: {}'.format(feed.name))
    solr.feedsolr.add([feed.to_solr()])
    return None
