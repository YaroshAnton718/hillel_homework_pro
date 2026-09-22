# AI Code Review

## 1. checkout

### Original code

```text
@login_required
def checkout(request):
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
```

### AI recommendations

AI reviewed the view and did not find any critical problems with the existing order creation logic.

The creation of `Order` and `OrderItem` objects is already wrapped in `transaction.atomic()`, so this part was left unchanged.

The main suggestion was to simplify the creation of Stripe `line_items`. Instead of creating an empty list and filling it with `append()`, the same logic can be written using a list comprehension.

A short docstring was also added to the view.

### Final code

```text
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
```

---

## 2. checkout_success

### Original code

```text
@login_required
def checkout_success(request):
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
```

### AI recommendations

For this view, the main point from the review was protection against repeated processing of the same successful payment.

The original version already checked that the order was not marked as paid before reducing the stock. However, two requests could theoretically reach this check at almost the same time.

The suggested change was to load the order with `select_for_update()` inside `transaction.atomic()`. This locks the order row while it is being processed and reduces the risk of the same payment being handled twice at the same time.

The cart clearing was also moved inside the block where the order is actually changed to `paid`.

A short docstring was added as well.

### Final code

```text
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
```

---

## 3. async_book_list

### Original code

```text
async def async_book_list(request):
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
```

### AI recommendations

The async ORM usage in this view was already correct.

The queryset is iterated asynchronously with `aiterator()`, so there was no reason to rewrite the view just for the sake of making changes.

The only change made after the review was adding a short docstring describing what the view does.

### Final code

```text
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
```