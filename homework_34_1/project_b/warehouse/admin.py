from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Shipment, ShipmentItem, StockItem, User


class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 0


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('book_id', 'title', 'quantity', 'updated_at')
    search_fields = ('title',)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'email', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'email')
    inlines = [ShipmentItemInline]