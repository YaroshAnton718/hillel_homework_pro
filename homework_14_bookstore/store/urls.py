from django.urls import path

from .views import (
    BookListView,
    BookDetailView,
    BookCreateView,
    BookUpdateView,
    BookDeleteView,
    RegisterView,
    BookLoginView,
    BookLogoutView,
    cart_detail,
    cart_add,
    cart_remove,
    cart_clear,
    checkout,
    checkout_success,
    async_book_list,
    async_book_detail,
    async_book_count,
)


app_name = 'store'


urlpatterns = [
    path(
        '',
        BookListView.as_view(),
        name='book_list'
    ),

    path(
        'async/books/',
        async_book_list,
        name='async_book_list'
    ),

    path(
        'async/books/count/',
        async_book_count,
        name='async_book_count'
    ),

    path(
        'async/book/<int:pk>/',
        async_book_detail,
        name='async_book_detail'
    ),

    path(
        'register/',
        RegisterView.as_view(),
        name='register'
    ),

    path(
        'login/',
        BookLoginView.as_view(),
        name='login'
    ),

    path(
        'logout/',
        BookLogoutView.as_view(),
        name='logout'
    ),

    path(
        'cart/',
        cart_detail,
        name='cart'
    ),

    path(
        'cart/add/<int:pk>/',
        cart_add,
        name='cart_add'
    ),

    path(
        'cart/remove/<int:pk>/',
        cart_remove,
        name='cart_remove'
    ),

    path(
        'cart/clear/',
        cart_clear,
        name='cart_clear'
    ),

    path(
        'checkout/',
        checkout,
        name='checkout'
    ),

    path(
        'checkout/success/',
        checkout_success,
        name='checkout_success'
    ),

    path(
        'book/<int:pk>/',
        BookDetailView.as_view(),
        name='book_detail'
    ),

    path(
        'book/create/',
        BookCreateView.as_view(),
        name='book_create'
    ),

    path(
        'book/<int:pk>/update/',
        BookUpdateView.as_view(),
        name='book_update'
    ),

    path(
        'book/<int:pk>/delete/',
        BookDeleteView.as_view(),
        name='book_delete'
    ),
]