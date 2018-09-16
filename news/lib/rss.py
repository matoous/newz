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
        fe.comments(link.url)
        fe.author(name=link.user.name)
        entries.append(fe)
    return entries

def rss_feed_builder(feed):
    fg = FeedGenerator()
    fg.id(feed.route)
    fg.title(feed.name)
    fg.link(feed.route, rel='self')
    fg.description(feed.description or "")
    fg.language(feed.lang)
    return fg

def rss_page(feed, links):
    fg = rss_feed_builder(feed)
    for entry in rss_entries(links):
        fg.add_entry(entry)
    return fg.rss_str(pretty=True)