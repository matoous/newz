from news.models.link import Link


class Search():
    def __init__(self, cls):
        self._cls = cls

        highlight_select = ['ts_headline(\'english\', "{}", plainto_tsquery(\'"{}"\')) AS {}_highlight'.format(column, "{q}", column) for column in self._cls.__searchable__]
        select_fields = self._cls.__fillable__ + highlight_select
        if self._cls.__timestamps__:
            select_fields += ['created_at', 'updated_at']
        self._select_statement = ", ".join(select_fields)

        # create where statement
        where_clauses = ['textsearchable_{} @@ to_tsquery(\'"{}"\')'.format(column, "{q}") for column in self._cls.__searchable__]
        self._where_statement = " OR ".join(where_clauses)

    def search(self, q):
        # parse query
        q = " & ".join(q.split())

        data = self._cls.select_raw(self._select_statement.format(q=q)).where_raw(self._where_statement.format(q=q)).order_by_raw('ups - downs DESC').get()
        return data


link_search = Search(Link)