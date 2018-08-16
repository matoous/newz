from news.models.link import Link


def archive_links():
    old_links = Link.where('archived', False).where_raw('created_at < NOW() - INTERVAL \'30 days\'').get()
    for link in old_links:
        link.archive()