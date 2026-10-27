from django.core.cache import cache
from django.shortcuts import get_object_or_404

from .models import StockItem

CACHE_TIMEOUT = 300


def stock_cache_key(book_id):
    return f'stock:{int(book_id)}'


def get_cached_stock(book_id):
    key = stock_cache_key(book_id)

    stock = cache.get(key)

    if stock is None:
        stock = get_object_or_404(StockItem, book_id=book_id)
        cache.set(key, stock, timeout=CACHE_TIMEOUT)

    return stock


def invalidate_stock_cache(book_id):
    cache.delete(stock_cache_key(book_id))