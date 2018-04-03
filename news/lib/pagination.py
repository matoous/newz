from flask import request


def paginate(links, page_size):
    count = request.args.get('count', default=0, type=int)
    start = min(count, len(links))
    end = min(start + page_size, len(links))
    return (links[start: end],
            max(0, start - page_size) if start > 0 else None,
            end if end < len(links) else None)
