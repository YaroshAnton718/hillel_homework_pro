from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache_utils import invalidate_stock_cache
from .models import StockItem


@receiver(post_save, sender=StockItem)
@receiver(post_delete, sender=StockItem)
def invalidate_stock_on_change(sender, instance, **kwargs):
    book_id = instance.book_id

    transaction.on_commit(lambda: invalidate_stock_cache(book_id))