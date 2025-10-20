# core/pagination.py
from rest_framework.pagination import PageNumberPagination

class DefaultPageNumberPagination(PageNumberPagination):
    """Paginación estándar: ?page=1&page_size=25 (máx 200)."""
    page_query_param = "page"
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200
