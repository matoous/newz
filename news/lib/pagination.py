from flask import request


def paginate(items, page_size):
    count = request.args.get("count", default=0, type=int)
    start = min(count, len(items))
    end = min(start + page_size, len(items))
    return (
        items[start:end],
        max(0, start - page_size) if start > 0 else None,
        end if end < len(items) else None,
    )
