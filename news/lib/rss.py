from feedgen.entry import FeedEntry
from feedgen.feed import FeedGenerator


def rss_entries(links, feed=None):
    entries = []
    for link in links:
        fe = FeedEntry()
        fe.title(link.title)
        fe.content(link.text)
        fe.summary("Post by {} in {}.".format(link.user.name, feed.name if feed else link.feed.name))
        fe.link(href=link.url)
        fe.published(link.created_at)
        fe.comments('http://localhost:5000/f/{}/{}'.format(feed.slug if feed else link.feed.slug, link.slug))
        fe.author(name=link.user.name)
        entries.append(fe)
    return entries

def rss_feed_builder(feed):
    fg = FeedGenerator()
    fg.id(feed.url)
    fg.title(feed.name)
    fg.link(href="http://localhost:5000" + feed.url, rel='self')
    fg.description(feed.description or "Hello, there is some description.")
    fg.language(feed.lang)
    return fg

def rss_page(feed, links):
    fg = rss_feed_builder(feed)
    for entry in rss_entries(links):
        fg.add_entry(entry)
    return fg.rss_str(pretty=True)