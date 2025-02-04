# utils/cache_utils.py
from django.conf import settings
from django.core.cache import cache



def get_or_set_cache(key, queryset, timeout=None):
    if not settings.CACHE_ENABLED:
        return queryset

    if timeout is None:
        timeout = settings.CACHE_TIMEOUT

    data = cache.get(key)

    if not data:
        data = queryset
        cache.set(key, data, timeout=timeout)

    return data
