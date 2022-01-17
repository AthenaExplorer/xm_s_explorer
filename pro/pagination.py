import math
from rest_framework.pagination import LimitOffsetPagination


class StandardResultsSetPagination(LimitOffsetPagination):
    def __init__(self, default_limit=20, max_limit=200):
        self.default_limit = default_limit
        self.limit_query_param = 'limit'
        self.offset_query_param = 'offset'
        self.max_limit = max_limit

    def get_next_link(self):
        offset = self.offset + self.limit
        return None if self.count < offset else offset

    def get_previous_link(self):
        return (self.offset - self.limit) if self.offset > 0 else None

    def get_total_pages(self):
        return math.ceil(self.count / self.limit)

    def get_paginated_response(self, data):
        return {
            'pages': self.get_total_pages(),
            'count': self.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        }