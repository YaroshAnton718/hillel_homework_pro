from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache_utils import (
    invalidate_book_cache,
    invalidate_category_cache,
)
from .models import Book, Category


@receiver(post_save, sender=Book)
@receiver(post_delete, sender=Book)
def invalidate_book_on_change(sender, instance, **kwargs):
    book_id = instance.pk

    transaction.on_commit(
        lambda: invalidate_book_cache(book_id)
    )


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_category_on_change(sender, instance, **kwargs):
    category_id = instance.pk

    transaction.on_commit(
        lambda: invalidate_category_cache(category_id)
    )
