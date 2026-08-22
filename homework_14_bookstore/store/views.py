from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .forms import RegisterForm
from .models import Book


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'store/register.html'
    success_url = reverse_lazy('store:login')


class BookLoginView(LoginView):
    template_name = 'store/login.html'


class BookLogoutView(LogoutView):
    pass


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


class BookCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView
):
    model = Book
    permission_required = 'store.manage_books'

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


class BookUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView
):
    model = Book
    permission_required = 'store.manage_books'

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


class BookDeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DeleteView
):
    model = Book
    permission_required = 'store.manage_books'

    template_name = 'store/book_confirm_delete.html'
    success_url = reverse_lazy('store:book_list')