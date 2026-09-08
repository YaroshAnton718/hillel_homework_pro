from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Book,
    Category,
    User,
    Order,
    OrderItem,
)


class BookInline(admin.TabularInline):
    model = Book
    extra = 1


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        'book',
        'quantity',
        'price',
        'subtotal',
    )

    @admin.display(description='Сума')
    def subtotal(self, obj):
        return obj.subtotal


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'is_staff',
        'is_active',
    )

    search_fields = (
        'username',
        'email',
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [BookInline]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'author',
        'price',
        'stock',
        'category'
    )

    list_filter = (
        'category',
        'author'
    )

    search_fields = (
        'title',
        'author',
        'description'
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'email',
        'total',
        'status',
        'created_at',
        'stripe_session_id',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'email',
        'user__username',
        'stripe_session_id',
    )

    readonly_fields = (
        'created_at',
        'stripe_session_id',
    )

    inlines = [OrderItemInline]