from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.conf import settings


class StandardResultsPagination(PageNumberPagination):
    """
    Переопределённый пагинатор, который добавляет общее количество страниц,
    ссылку на следующую и предыдущую страницы и возвращает результаты.
    """
    page_size = getattr(settings, 'REST_FRAMEWORK_PAGE_SIZE', 10)
    page_size_query_param = 'limit'
    max_page_size = getattr(settings, 'REST_FRAMEWORK_MAX_PAGE_SIZE', 100)
