import time

from flask import request, render_template

from news.lib.db.search import link_search


def search():
    q = request.args.get('q')

    start = time.perf_counter()

    links = link_search.search(q)

    end = time.perf_counter()

    search_info = {
        'elapsed': "{0:.2f}".format(end - start),
        'hits': links[0].full_count if len(links) > 0 else 0,
    }

    return render_template("search.html", links=links, q=q, search_info=search_info)
