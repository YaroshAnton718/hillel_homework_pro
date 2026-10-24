import uuid

from django.core.cache import cache
from django.shortcuts import get_object_or_404

from .models import Book

CACHE_TIMEOUT = 300

BOOKS_VERSION_KEY = 'books:version'


def get_books_cache_version():
    return cache.get(BOOKS_VERSION_KEY, 'initial')


def invalidate_books_version():
    cache.set(BOOKS_VERSION_KEY, uuid.uuid4().hex, timeout=None)


def get_cached_book(book_id):
    cache_key = f'book:detail:{book_id}'

    book = cache.get(cache_key)

    if book is None:
        book = get_object_or_404(Book.objects.select_related('category'), pk=book_id)

        cache.set(cache_key, book, timeout=CACHE_TIMEOUT)

    return book


def invalidate_book_cache(book_id):
    cache.delete(f'book:detail:{book_id}')

    invalidate_books_version()


def invalidate_category_cache(category_id):
    book_ids = Book.objects.filter(category_id=category_id).values_list('id', flat=True)

    cache.delete_many([f'book:detail:{book_id}' for book_id in book_ids])

    invalidate_books_version()
