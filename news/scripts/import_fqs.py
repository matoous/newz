from datetime import datetime, timedelta


BATCH_SIZE = 100
AUTOPOSTER_ID = 12345


def import_fqs():
    from news.models.link import Link
    from news.models.fully_qualified_source import FullyQualifiedSource
    print('Importing Fully Qualified Sources')
    while True:
        # Get batch of FQS
        now = datetime.now()
        sources = FullyQualifiedSource.where('next_update', '<', now).limit(BATCH_SIZE).get()

        # No FQS left to check
        if not sources or sources == []:
            print('Finished')
            break

        # Check FQS
        for source in sources:
            print('Source {}'.format(source.url))
            try:
                articles = source.get_links()
            except Exception as e:
                print("couldn't get links for FQS {}, error: {}".format(source.url, e))
                articles = []
            for article in articles:
                # skip if article already posted
                if Link.by_slug(article['slug']) is not None:
                    continue
                link = Link(title=article['title'],
                            slug=article['slug'],
                            text=article['text'],
                            url=article['url'],
                            feed_id=source.feed_id,
                            user_id=AUTOPOSTER_ID)
                link.commit()
            source.next_update = now + timedelta(seconds=source.update_interval)
            source.save()
