from .models import Book


class Cart:
    SESSION_KEY = 'cart'

    def __init__(self, request):
        self.session = request.session

        cart = self.session.get(self.SESSION_KEY)

        if cart is None:
            cart = {}
            self.session[self.SESSION_KEY] = cart

        self.cart = cart

    def add(self, book, quantity=1):
        book_id = str(book.id)

        if book_id not in self.cart:
            self.cart[book_id] = 0

        self.cart[book_id] += quantity

        if self.cart[book_id] <= 0:
            del self.cart[book_id]

        self.save()

    def remove(self, book):
        book_id = str(book.id)

        if book_id in self.cart:
            del self.cart[book_id]
            self.save()

    def clear(self):
        self.cart = {}
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True

    def save(self):
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True

    def __iter__(self):
        book_ids = self.cart.keys()

        books = Book.objects.filter(
            id__in=book_ids
        ).select_related('category')

        books_by_id = {
            str(book.id): book
            for book in books
        }

        for book_id, quantity in self.cart.items():
            book = books_by_id.get(book_id)

            if book is None:
                continue

            yield {
                'book': book,
                'quantity': quantity,
                'price': book.price,
                'total_price': book.price * quantity,
            }

    def __len__(self):
        return sum(self.cart.values())

    def get_total_price(self):
        return sum(
            item['total_price']
            for item in self
        )