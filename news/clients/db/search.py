from datetime import datetime, timedelta

from news.models.feed import Feed
from news.models.link import Link


def time_string_to_timedelta(timestr):
    return {
        "day": timedelta(days=1),
        "week": timedelta(days=7),
        "month": timedelta(days=31),
        "year": timedelta(days=365),
    }[timestr]


class Search:
    """
    Search
    """

    def __init__(self, cls, sorts, default_sort=None):
        self._cls = cls
        self._sorts = sorts
        self._default_sort = default_sort

        # prepare select statement with highlighting
        highlight_select = [
            "ts_headline('english', \"{}\", plainto_tsquery('english', '\"{}\"')) AS {}_highlight".format(
                column, "{q}", column
            )
            for column in self._cls.__searchable__
        ]
        select_fields = ["*"] + highlight_select + ["count(*) OVER() AS full_count"]
        if self._cls.__timestamps__:
            select_fields += ["created_at", "updated_at"]
        self._select_statement = ", ".join(select_fields)

        # create where statement
        where_clauses = [
            "textsearchable_{} @@ to_tsquery('english', '{}')".format(column, "{q}")
            for column in self._cls.__searchable__
        ]
        self._where_statement = " OR ".join(where_clauses)

    def search(self, q, sort=None, time=None):
        # parse query
        q = " & ".join(q.split())

        data = self._cls.select_raw(self._select_statement.format(q=q))

        if time is None or time is "all":
            data = data.where_raw(self._where_statement.format(q=q))
        else:
            data = data.where_raw(
                "({}) AND created_at >= {}".format(
                    self._where_statement.format(q=q),
                    datetime.utcnow() - time_string_to_timedelta(time),
                )
            )

        if sort in self._sorts:
            data = data.order_by_raw(self._sorts[sort])

        data = data.limit(30)

        return data.get()


link_search = Search(
    Link, sorts={"score": "ups - downs DESC", "comments": "comments_count DESC"}
)

feed_search = Search(Feed, sorts={"subscribers": "subscribers_count DESC"})
