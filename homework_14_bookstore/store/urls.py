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
)

app_name = 'store'

urlpatterns = [
    path('', BookListView.as_view(), name='book_list'),

    path('register/', RegisterView.as_view(), name='register'),

    path('login/', BookLoginView.as_view(), name='login'),

    path('logout/', BookLogoutView.as_view(), name='logout'),

    path('book/<int:pk>/', BookDetailView.as_view(), name='book_detail'),

    path('book/create/', BookCreateView.as_view(), name='book_create'),

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