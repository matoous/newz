import time

from flask import request, render_template

from news.clients.db.search import link_search, feed_search


def search():
    q = request.args.get("q")

    start = time.perf_counter()

    links = link_search.search(q)
    feeds = feed_search.search(q)

    end = time.perf_counter()

    hits = sum([x[0].full_count if len(x) > 0 else 0 for x in [links, feeds]])

    search_info = {"elapsed": "{0:.3f}".format(end - start), "hits": hits}

    return render_template(
        "search.html", links=links, q=q, search_info=search_info, feeds=feeds
    )
