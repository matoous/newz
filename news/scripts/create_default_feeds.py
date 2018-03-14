from slugify import slugify

from news.models.feed import Feed
from news.models.link import Link
from news.models.user import User


def create_default_feeds():
    u = User(username='matoous', email='matdz@seznam.cz')
    u.set_password('lokiloki')
    try:
        u.save()
    except:
        u = User.where('id', 1).first()

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

    f = Feed.where('slug', 'hackernews').first()
    l = Link(title='Why Pi Matters',
             slug=slugify('Why Pi Matters'),
             summary='Every March 14th, mathematicians like me are prodded out of our burrows like Punxsutawney Phil '
                     'on Groundhog Day, blinking and bewildered by all the fuss. Yes, it’s Pi Day again. And not just '
                     'any Pi Day. They’re calling this the Pi Day of the century: 3.14.15. Pi to five digits. A '
                     'once-in-a-lifetime thing.',
             url='https://www.newyorker.com/tech/elements/pi-day-why-pi-matters',
             feed_id=f.id,
             user_id=u.id)
    l.save()
    l2 = Link(title='Reddit and the Struggle to Detoxify the Internet',
              slug=slugify('Reddit and the Struggle to Detoxify the Internet'),
              summary='How do we fix life online without limiting free speech?',
              url='https://www.newyorker.com/magazine/2018/03/19/reddit-and-the-struggle-to-detoxify-the-internet',
              feed_id=f.id,
              user_id=u.id)
    l2.save()