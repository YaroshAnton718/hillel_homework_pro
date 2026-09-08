from decimal import Decimal

import stripe

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


def cart_detail(request):
    cart = Cart(request)

    return render(
        request,
        'store/cart.html',
        {
            'cart': cart,
        }
    )


def cart_add(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        if quantity > 0:
            cart = Cart(request)
            cart.add(book, quantity)

    return redirect('store:cart')


def cart_remove(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        cart = Cart(request)
        cart.remove(book)

    return redirect('store:cart')


def cart_clear(request):
    if request.method == 'POST':
        cart = Cart(request)
        cart.clear()

    return redirect('store:cart')


@login_required
def checkout(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.error(
            request,
            'Кошик порожній.'
        )
        return redirect('store:cart')

    for item in cart:
        if item['quantity'] > item['book'].stock:
            messages.error(
                request,
                f'Недостатньо товару: {item["book"].title}.'
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
        subject=f'Нове замовлення #{order.pk}',
        message=(
            f'Дякуємо за замовлення #{order.pk}.\n\n'
            f'Сума замовлення: {order.total} UAH.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=False,
    )

    line_items = []

    for item in cart:
        line_items.append({
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
        })

    checkout_session = stripe.checkout.Session.create(
        mode='payment',
        line_items=line_items,
        customer_email=order.email,
        success_url=(
            f'{settings.SITE_URL}'
            f'/checkout/success/?session_id={{CHECKOUT_SESSION_ID}}'
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


def checkout_success(request):
    session_id = request.GET.get('session_id')

    if not session_id:
        return redirect('store:book_list')

    checkout_session = stripe.checkout.Session.retrieve(
        session_id
    )

    order_id = checkout_session.metadata.to_dict().get('order_id')

    if not order_id:
        return redirect('store:book_list')

    order = get_object_or_404(
        Order,
        pk=order_id,
        user=request.user,
    )

    if (
        checkout_session.payment_status == 'paid'
        and order.status != Order.STATUS_PAID
    ):
        with transaction.atomic():
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

    return render(
        request,
        'store/checkout_success.html',
        {
            'order': order,
        }
    )