from slugify import slugify

from news.models.feed import Feed
from news.models.link import Link
from news.models.user import User


def create_default_feeds():
    u = User(username='matoous', email='matdz@seznam.cz')
    u1 = User(username='test', email='test@test.te')
    u2 = User(username='test2', email='test2@test.te')
    u.set_password('lokiloki')
    u1.set_password('testtest')
    u2.set_password('testtest')
    try:
        u.save()
        u1.save()
        u2.save()
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
                  slug=slugify("Hackernews")),
             Feed(name="Testfeed",
                  description="The Testing Feed",
                  slug=slugify("Testfeed"))
             ]
    for feed in feeds:
        try:
            feed.save()
        except:
            pass

    f = Feed.where('slug', 'hackernews').first()
    l = Link(title='Why Pi Matters',
             slug=slugify('Why Pi Matters'),
             text='Every March 14th, mathematicians like me are prodded out of our burrows like Punxsutawney Phil '
                     'on Groundhog Day, blinking and bewildered by all the fuss. Yes, it’s Pi Day again. And not just '
                     'any Pi Day. They’re calling this the Pi Day of the century: 3.14.15. Pi to five digits. A '
                     'once-in-a-lifetime thing.',
             url='https://www.newyorker.com/tech/elements/pi-day-why-pi-matters',
             feed_id=f.id,
             user_id=u.id)
    try:
        l.commit()
    except:
        pass
    l2 = Link(title='Reddit and the Struggle to Detoxify the Internet',
              slug=slugify('Reddit and the Struggle to Detoxify the Internet'),
              text='How do we fix life online without limiting free speech?',
              url='https://www.newyorker.com/magazine/2018/03/19/reddit-and-the-struggle-to-detoxify-the-internet',
              feed_id=f.id,
              user_id=u.id)
    try:
        l2.commit()
    except:
        pass
    f = Feed.where('slug', 'the-awesome-earth').first()
    l3 = Link(title='Is This the Underground Everest?',
              slug=slugify('Is This the Underground Everest?'),
              text='Far beneath a remote mountain range in Uzbekistan, explorers are delving into a labyrinth that could be the world\'s deepest cave.',
              url='https://www.nationalgeographic.com/magazine/2017/03/dark-star-deepest-cave-climbing-uzbekistan/',
              feed_id=f.id,
              user_id=u.id)
    try:
        l3.commit()
    except:
        pass

    f = Feed.where('slug', 'good-long-reads').first()
    l4 = Link(title='The Man Who’s Helped Elon Musk, Tom Brady, and Ari Emanuel Get Dressed',
              slug=slugify('The Man Who’s Helped Elon Musk, Tom Brady, and Ari Emanuel Get Dressed'),
              text='Andrew Weitz spruces up Hollywood’s reluctant Zoolanders.',
              url='https://www.newyorker.com/magazine/2018/03/19/the-man-whos-helped-elon-musk-tom-brady-and-ari-emanuel-get-dressed',
              feed_id=f.id,
              user_id=u.id)
    try:
        l4.commit()
    except:
        pass

    f = Feed.where('slug', 'testfeed').first()

    import feedparser
    d = feedparser.parse('https://news.ycombinator.com/rss')
    for entry in d['entries']:
        ll = Link(title=entry['title'],
                  slug=slugify(entry['title']),
                  summary='',
                  url=entry['link'],
                  feed_id=f.id,
                  user_id=u.id)
        try:
            ll.commit()
        except Exception as e:
            pass

def importHN():
    import feedparser
    u = User.where('id', 1).first()
    f = Feed.where('slug', 'testfeed').first()
    d = feedparser.parse('https://news.nationalgeographic.com/news/misc/rss')
    # https://news.ycombinator.com/rss
    # https://news.nationalgeographic.com/news/misc/rss
    for entry in d['entries']:
        ll = Link(title=entry['title'],
                  slug=slugify(entry['title']),
                  text='',
                  url=entry['link'],
                  feed_id=f.id,
                  user_id=u.id)
        try:
            ll.commit()
        except Exception as e:
            pass