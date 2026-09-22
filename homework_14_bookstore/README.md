# BookStore

BookStore is a Django project for a simple online bookstore.

Users can browse books, filter them by category, add books to a cart, create orders, and pay through Stripe.

## Features

Main features:

* user registration, login, and logout;
* book list and book detail pages;
* filtering and pagination;
* creating, editing, and deleting books with permissions;
* shopping cart;
* order creation;
* Stripe Checkout;
* email notification after creating an order;
* stock update after successful payment;
* Ukrainian and English languages;
* async views;
* unit and integration tests.

## Technologies

The project uses:

* Python;
* Django;
* PostgreSQL;
* Docker and Docker Compose;
* Stripe;
* Bootstrap;
* pytest;
* pytest-django;
* pytest-asyncio;
* pytest-cov;
* factory-boy.

## Project Structure

```text
bookstore/
├── bookstore/
├── store/
│   ├── migrations/
│   ├── static/
│   ├── templates/
│   ├── admin.py
│   ├── cart.py
│   ├── forms.py
│   ├── middleware.py
│   ├── models.py
│   ├── queries.py
│   ├── urls.py
│   └── views.py
├── tests/
├── locale/
├── AI_PROMPTS.md
├── AI_REVIEW.md
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
└── requirements.txt
```

## Models

The project has the following main models:

* `User` — custom user model based on `AbstractUser`;
* `Category` — book category;
* `Book` — book information, price, stock, author and category;
* `Order` — customer order;
* `OrderItem` — separate item inside an order.

Book management uses a custom permission:

```text
store.manage_books
```

## Async Views

There are three async views:

```text
async_book_list
async_book_detail
async_book_count
```

They use Django async ORM methods such as `aiterator()`, `aget()` and `acount()`.

## Internationalization

The project supports Ukrainian and English.

Translation files are stored in:

```text
locale/uk/LC_MESSAGES/
locale/en/LC_MESSAGES/
```

## Stripe

Stripe is used for checkout.

When a user starts checkout, the application creates an order and its items, sends an email, creates a Stripe Checkout Session and redirects the user to Stripe.

After successful payment, the order is marked as paid and book stock is reduced.

`select_for_update()` is used while processing a paid order.

## Running

Start the project with Docker:

```bash
docker compose up --build
```

Stop it with:

```bash
docker compose down
```

Migrations are applied automatically when the container starts.

## Tests

Run tests with:

```bash
docker compose exec web pytest
```

The project contains unit, integration and async tests.

Coverage is configured in `pytest.ini`. The minimum project coverage is set to 70%.

## AI Usage

AI was used for several parts of the assignment.

### Code Review

Three views were reviewed:

* `checkout`;
* `checkout_success`;
* `async_book_list`.

For `checkout`, the Stripe `line_items` code was simplified.

For `checkout_success`, `select_for_update()` was added to help prevent repeated processing of the same order.

The async implementation of `async_book_list` was also reviewed.

More details are in:

```text
AI_REVIEW.md
```

### AI Tests

AI was used to generate additional tests for:

* `Category`;
* `Book`;
* `Order`.

They are stored in:

```text
tests/test_ai_models.py
```

Each generated test contains:

```text
Generated with AI, reviewed and modified
```

### Documentation

AI was used to generate short docstrings for views and to help update this README.

The prompts used during the task are stored in:

```text
AI_PROMPTS.md
```
