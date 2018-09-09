from rq.decorators import job

from news.lib.db.query import LinkQuery
from news.lib.task_queue import redis_conn


@job('medium', connection=redis_conn)
def update_link(updated_link):
    """
    Update link score
    :param updated_link: link to update
    :return: nothing
    """
    for sort in ['trending', 'best']:  # no need to update 'new' because it doesn't depend on score
        LinkQuery(feed_id=updated_link.feed_id, sort=sort).insert([updated_link])
    return None
