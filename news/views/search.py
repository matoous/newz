import time

from flask import request, render_template

from news.lib.solr import solr
from news.models.feed import Feed
from news.models.link import Link


def search():
    q = request.args.get('q')

    start = time.perf_counter()

    result_links = solr.search_links(q)
    result_feeds = solr.search_feeds(q)

    end = time.perf_counter()

    search_result_links = []
    for seach_result in result_links:
        highlight = result_links.highlighting[seach_result['id']]
        link = Link.by_id(int(seach_result['id']))
        search_result_links.append({
            "link": link,
            "title": highlight['title'][0] if highlight and 'title' in highlight else None,
            "text": highlight['text'][0] if highlight and 'text' in highlight else None,
            "url": highlight['url'][0] if highlight and 'url' in highlight else None,
        })

    search_result_feeds = []
    for seach_result in result_feeds:
        highlight = result_feeds.highlighting[seach_result['id']]
        feed = Feed.by_id(int(seach_result['id']))
        search_result_feeds.append({
            "feed": feed,
            "name": highlight['name'][0] if highlight and 'name' in highlight else None,
            "description": highlight['description'][0] if highlight and 'description' in highlight else None,
        })

    search_info = {
        'elapsed': "{0:.2f}".format(end - start),
        'hits': result_links.hits + result_feeds.hits,
    }

    return render_template("search.html", links=search_result_links, feeds=search_result_feeds, q=q, search_info=search_info)
