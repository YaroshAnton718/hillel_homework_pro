# BookStore

[![Django CI](https://github.com/YaroshAnton718/hillel_homework_pro/actions/workflows/django.yml/badge.svg)](https://github.com/YaroshAnton718/hillel_homework_pro/actions/workflows/django.yml)
[![codecov](https://codecov.io/gh/YaroshAnton718/hillel_homework_pro/branch/main/graph/badge.svg)](https://codecov.io/gh/YaroshAnton718/hillel_homework_pro)

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
* health check endpoint;
* unit and integration tests;
* CI/CD with GitHub Actions.

## Technologies

The project uses:

* Python;
* Django;
* PostgreSQL;
* Redis;
* Celery;
* Gunicorn;
* WhiteNoise;
* Docker and Docker Compose;
* GitHub Actions;
* Stripe;
* Bootstrap;
* pytest;
* pytest-django;
* pytest-asyncio;
* pytest-cov;
* factory-boy;
* flake8 and black.

## Project Structure

```text
bookstore/
├── .github/
│   └── workflows/
│       └── django.yml
├── bookstore/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── health.py
│   └── urls.py
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
├── nginx/
├── AI_PROMPTS.md
├── AI_REVIEW.md
├── .env.example
├── .flake8
├── docker-compose.yml
├── Dockerfile
├── gunicorn.conf.py
├── pyproject.toml
├── pytest.ini
├── render.yaml
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

## Settings

Settings are split into three modules:

| Module | Purpose |
|---|---|
| `bookstore.settings.base` | Common settings |
| `bookstore.settings.development` | Local development and tests (`DEBUG`, debug toolbar) |
| `bookstore.settings.production` | Production (`DEBUG=False`, security headers, WhiteNoise) |

The active module is chosen with the `DJANGO_SETTINGS_MODULE` environment variable.
`manage.py` and `pytest.ini` use `development` by default. `wsgi.py`, `asgi.py` and `celery.py` use `production` by default.

Production security settings include:

* `DEBUG = False`;
* HTTPS redirect (`SECURE_SSL_REDIRECT`);
* secure session and CSRF cookies;
* HSTS;
* `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`.

All secrets and environment-specific values are read from environment variables. See `.env.example` for the full list.

## Health Check

```text
GET /health/
```

The endpoint checks the database and the cache.

Healthy response (`200`):

```json
{"status": "ok", "database": "ok", "cache": "ok"}
```

If any check fails, the endpoint returns `503`.

## Running

Create a local `.env` file based on `.env.example` (for local development set `DJANGO_SETTINGS_MODULE=bookstore.settings.development`).

Start the project with Docker:

```bash
docker compose up --build
```

The application is available at http://localhost:8000.

Stop it with:

```bash
docker compose down
```

Migrations are applied automatically when the container starts.

Gunicorn is configured in `gunicorn.conf.py`. The number of workers is set with `WEB_CONCURRENCY`, the port with `PORT`.

Static files are served by WhiteNoise in production and by nginx in the local Docker setup.

## Tests

Run tests with:

```bash
docker compose exec web pytest
```

The project contains unit, integration and async tests.

Coverage is configured in `pytest.ini`. The minimum project coverage is set to 70%.

## Linting

```bash
black .
flake8 .
```

## CI/CD

The pipeline is defined in `.github/workflows/django.yml` and runs on every push and pull request to `main`:

1. **lint** — `flake8` and `black --check`;
2. **test** — `pytest` with coverage (PostgreSQL and Redis as services), coverage is uploaded to Codecov;
3. **docker** — builds the Docker image and pushes it to Docker Hub (only on push to `main`).

Required GitHub Secrets:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
CODECOV_TOKEN
```

The image is published as `<DOCKERHUB_USERNAME>/bookstore` with tags `latest` and the commit SHA.

## Deployment (Render)

The project is deployed to Render using `render.yaml` (Blueprint). It creates:

* a web service (Docker, Gunicorn);
* a PostgreSQL database;
* a Redis (Key Value) instance.

Steps:

1. Render → **New → Blueprint** → select this repository.
2. Fill in the variables marked `sync: false` (`SITE_URL`, `STRIPE_SECRET_KEY`, `EMAIL_*`).
3. Apply the Blueprint and wait for the build.
4. Check `https://<service>.onrender.com/health/`.

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