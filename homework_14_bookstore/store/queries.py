from django.db.models import Q, Count, Avg
from .models import Book, Category

def get_available_books():
    return Book.objects.filter(stock__gt=0)

def search_books():
    return Book.objects.filter(
        Q(title__icontains="python") |
        Q(author__icontains="django")
    )

def categories_with_book_count():
    return Category.objects.annotate(
        books_count=Count("books")
    )

def categories_with_average_price():
    return Category.objects.annotate(
        avg_price=Avg("books__price")
    )