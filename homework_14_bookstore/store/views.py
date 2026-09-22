from decimal import Decimal

import stripe

from asgiref.sync import sync_to_async

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .cart import Cart
from .forms import RegisterForm
from .models import Book, Order, OrderItem


stripe.api_key = settings.STRIPE_SECRET_KEY


class RegisterView(CreateView):
    """Register a new user account."""

    form_class = RegisterForm
    template_name = 'store/register.html'
    success_url = reverse_lazy('store:login')


class BookLoginView(LoginView):
    """Authenticate a user and log them into the bookstore."""

    template_name = 'store/login.html'


class BookLogoutView(LogoutView):
    """Log the current user out of the bookstore."""


class BookListView(ListView):
    """Display a paginated list of books with optional category filtering."""

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
    """Display detailed information about a single book."""

    model = Book
    template_name = 'store/book_detail.html'
    context_object_name = 'book'


class BookCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView
):
    """Allow authorized users to create a new book."""

    model = Book
    permission_required = 'store.manage_books'

    fields = [
        'category',
        'title',
        'author',
        'price',
        'description',
        'stock',
    ]

    template_name = 'store/book_form.html'
    success_url = reverse_lazy('store:book_list')


class BookUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView
):
    """Allow authorized users to update an existing book."""

    model = Book
    permission_required = 'store.manage_books'

    fields = [
        'category',
        'title',
        'author',
        'price',
        'description',
        'stock',
    ]

    template_name = 'store/book_form.html'
    success_url = reverse_lazy('store:book_list')


class BookDeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DeleteView
):
    """Allow authorized users to delete an existing book."""

    model = Book
    permission_required = 'store.manage_books'

    template_name = 'store/book_confirm_delete.html'
    success_url = reverse_lazy('store:book_list')


async def async_book_list(request):
    """Return the book list using asynchronous database iteration."""

    books = []

    async for book in (
        Book.objects
        .select_related('category')
        .order_by('id')
        .aiterator()
    ):
        books.append(book)

    return await sync_to_async(render)(
        request,
        'store/async_book_list.html',
        {
            'books': books,
        }
    )


async def async_book_detail(request, pk):
    """Return details of a single book using an asynchronous query."""

    book = await Book.objects.select_related(
        'category'
    ).aget(pk=pk)

    return await sync_to_async(render)(
        request,
        'store/async_book_detail.html',
        {
            'book': book,
        }
    )


async def async_book_count(request):
    """Return the total number of books using an asynchronous query."""

    count = await Book.objects.acount()

    return await sync_to_async(render)(
        request,
        'store/async_book_count.html',
        {
            'count': count,
        }
    )


def cart_detail(request):
    """Display the current shopping cart."""

    cart = Cart(request)

    return render(
        request,
        'store/cart.html',
        {
            'cart': cart,
        }
    )


def cart_add(request, pk):
    """Add a selected book and quantity to the shopping cart."""

    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        try:
            quantity = int(
                request.POST.get('quantity', 1)
            )
        except (TypeError, ValueError):
            quantity = 1

        if quantity > 0:
            cart = Cart(request)
            cart.add(book, quantity)

    return redirect('store:cart')


def cart_remove(request, pk):
    """Remove a selected book from the shopping cart."""

    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        cart = Cart(request)
        cart.remove(book)

    return redirect('store:cart')


def cart_clear(request):
    """Clear all items from the shopping cart."""

    if request.method == 'POST':
        cart = Cart(request)
        cart.clear()

    return redirect('store:cart')


@login_required
def checkout(request):
    """Create an order and redirect the authenticated user to Stripe Checkout."""

    cart = Cart(request)

    if len(cart) == 0:
        messages.error(
            request,
            _('Cart is empty.')
        )
        return redirect('store:cart')

    for item in cart:
        if item['quantity'] > item['book'].stock:
            messages.error(
                request,
                _(
                    'Not enough stock: %(title)s.'
                ) % {
                    'title': item['book'].title
                }
            )
            return redirect('store:cart')

    total = cart.get_total_price()

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            email=request.user.email,
            total=total,
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                book=item['book'],
                quantity=item['quantity'],
                price=item['price'],
            )

    send_mail(
        subject=_('New order #%(id)s') % {
            'id': order.pk
        },
        message=_(
            'Thank you for your order #%(id)s.\n\n'
            'Order total: %(total)s UAH.'
        ) % {
            'id': order.pk,
            'total': order.total,
        },
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=False,
    )

    line_items = [
        {
            'price_data': {
                'currency': settings.STRIPE_CURRENCY,
                'product_data': {
                    'name': item['book'].title,
                },
                'unit_amount': int(
                    item['price'] * Decimal('100')
                ),
            },
            'quantity': item['quantity'],
        }
        for item in cart
    ]

    checkout_session = stripe.checkout.Session.create(
        mode='payment',
        line_items=line_items,
        customer_email=order.email,
        success_url=(
            f'{settings.SITE_URL}'
            f'/checkout/success/'
            f'?session_id={{CHECKOUT_SESSION_ID}}'
        ),
        cancel_url=f'{settings.SITE_URL}/cart/',
        metadata={
            'order_id': str(order.pk),
        },
    )

    order.stripe_session_id = checkout_session.id

    order.save(
        update_fields=['stripe_session_id']
    )

    return redirect(
        checkout_session.url,
        permanent=False,
    )


@login_required
def checkout_success(request):
    """Confirm a successful Stripe payment and update the related order."""

    session_id = request.GET.get('session_id')

    if not session_id:
        return redirect('store:book_list')

    checkout_session = stripe.checkout.Session.retrieve(
        session_id
    )

    order_id = (
        checkout_session.metadata
        .to_dict()
        .get('order_id')
    )

    if not order_id:
        return redirect('store:book_list')

    if checkout_session.payment_status == 'paid':
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                pk=order_id,
                user=request.user,
            )

            if order.status != Order.STATUS_PAID:
                order.status = Order.STATUS_PAID

                order.save(
                    update_fields=['status']
                )

                for item in order.items.select_related('book'):
                    item.book.stock -= item.quantity

                    item.book.save(
                        update_fields=['stock']
                    )

                Cart(request).clear()

    else:
        order = get_object_or_404(
            Order,
            pk=order_id,
            user=request.user,
        )

    return render(
        request,
        'store/checkout_success.html',
        {
            'order': order,
        }
    )