from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)

from .models import Book


class BookListView(ListView):
    model = Book
    template_name = 'store/book_list.html'
    context_object_name = 'books'
    paginate_by = 5

    def get_queryset(self):
        queryset = Book.objects.select_related('category')

        category = self.request.GET.get('category')

        if category:
            queryset = queryset.filter(category_id=category)

        return queryset


class BookDetailView(DetailView):
    model = Book
    template_name = 'store/book_detail.html'
    context_object_name = 'book'


class BookCreateView(CreateView):
    model = Book
    fields = [
        'category',
        'title',
        'author',
        'price',
        'description',
        'stock'
    ]
    template_name = 'store/book_form.html'
    success_url = reverse_lazy('store:book_list')


class BookUpdateView(UpdateView):
    model = Book
    fields = [
        'category',
        'title',
        'author',
        'price',
        'description',
        'stock'
    ]
    template_name = 'store/book_form.html'
    success_url = reverse_lazy('store:book_list')


class BookDeleteView(DeleteView):
    model = Book
    template_name = 'store/book_confirm_delete.html'
    success_url = reverse_lazy('store:book_list')