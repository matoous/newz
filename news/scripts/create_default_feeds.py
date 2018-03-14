from slugify import slugify

from news.models.feed import Feed


def create_default_feeds():
    feeds = [Feed(name="Good long reads",
                  description="Good long articles for you to waste time and learn something new.",
                  slug=slugify("Good long reads")),
             Feed(name="The Awesome Earth",
                  description="",
                  slug=slugify("The Awesome Earth")),
             Feed(name="Wildlife",
                  description="",
                  slug=slugify("Wildlife")),
             Feed(name="Python",
                  description="",
                  slug=slugify("Python")),
             Feed(name="Golang",
                  description="",
                  slug=slugify("Golang")),
             Feed(name="Hackernews",
                  description="",
                  slug=slugify("Hackernews"))
             ]
    for feed in feeds:
        feed.save()