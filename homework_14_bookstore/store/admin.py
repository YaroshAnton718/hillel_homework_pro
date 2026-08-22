from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Book, Category, User


class BookInline(admin.TabularInline):
    model = Book
    extra = 1


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