import time

from flask import Blueprint, request, redirect, render_template

from news.lib.solr import linksolr
from news.models.link import Link

search_blueprint = Blueprint('search', __name__, template_folder='/templates')


@search_blueprint.route('/search')
def search():
    q = request.args.get('q')

    start = time.perf_counter()
    x = linksolr.search('text:{} title:{}'.format(q,q), **{
        'hl.fl': '*',
        'hl': 'on',
        'hl.snippets': 1,
        'hl.fragsize': 0,
    })
    end = time.perf_counter()

    search_result_links = []
    for seach_result in x:
        highlight = x.highlighting[seach_result['id']]
        link = Link.by_id(int(seach_result['id']))
        search_result_links.append(
            {
                "link": link,
                "title": highlight['title'][0] if highlight and 'title' in highlight else None,
                "text": highlight['text'][0] if highlight and 'text' in highlight else None,
                "url": highlight['url'][0] if highlight and 'url' in highlight else None,
            }
        )

    return render_template("search.html", links=search_result_links, q=q, elapsed="{0:.2f}".format(end-start))

