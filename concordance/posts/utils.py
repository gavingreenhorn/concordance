from django.core.paginator import Paginator
from django.conf import settings


def get_page_obj(query_set, page_number, page_size=settings.POSTS_PER_PAGE):
    paginator = Paginator(query_set, settings.POSTS_PER_PAGE)
    return paginator.get_page(page_number)
