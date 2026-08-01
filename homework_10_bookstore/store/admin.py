from django.contrib import admin
from .models import Book, Category

class BookInline(admin.TabularInline):
    model = Book
    extra = 1

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