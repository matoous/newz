#  raw queries for time filtering entries
#  usage: .where_raw(time_filters['filter_type'])

"""
Filters for database queries to filter by object age
"""
time_filters = {
    "day": "created_at >= date_trunc('day', now())",
    "month": "created_at >= date_trunc('month', now())",
    "year": "created_at >= date_trunc('year', now())",
}
