import time

from flask import request, render_template

from news.models.link import Link


def search():
    q = request.args.get('q')


    start = time.perf_counter()

    links = Link.search(q)
    for l in links:
        print(l)
        print(l.title_highlight)
        print(l.text_highlight)

    end = time.perf_counter()

    search_info = {
        'elapsed': "{0:.2f}".format(end - start),
        'hits': len(links),
    }

    return render_template("search.html", links=links, q=q, search_info=search_info)
