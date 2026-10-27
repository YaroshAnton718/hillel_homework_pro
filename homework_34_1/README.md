# BookStore & Warehouse

An educational project consisting of two Django services: an online bookstore and a warehouse management service.

## Project Structure

- **ProjectA (`project_a`)** — an online bookstore with books, a shopping cart, orders, and Stripe payments.
- **ProjectB (`project_b`)** — a warehouse service for inventory, stock reservations, shipments, and order processing.

ProjectA communicates with ProjectB through a REST API.

## Technologies

- Python, Django, Django REST Framework
- PostgreSQL, Redis, Celery
- Docker Compose, NGINX, Gunicorn
- JWT Authentication
- Bootstrap, pytest, pytest-cov
- GitHub Actions

```

## Main Features

- User registration and authentication.
- Roles, groups, and permissions.
- Book catalog, shopping cart, order creation, and payments.
- Warehouse inventory management and stock reservations.
- JWT authentication for API endpoints.
- Background tasks with Celery.
- Redis caching.
- Ukrainian and English language support.
- Error handling and logging for inter-service requests.
- Health check endpoints.

## Running the Project

Install Docker Desktop and make sure Docker is running.

Start all services:

```bash
docker compose up --build -d
```

Check the container status:

```bash
docker compose ps
```

Check the APIs:

- ProjectA: http://localhost:8000/health/
- ProjectB: http://localhost:8001/health/

Stop the services:

```bash
docker compose down
```

## Testing

Run ProjectA tests:

```bash
docker compose exec web-a pytest -v
```

Run ProjectB tests:

```bash
docker compose exec web-b pytest -v -o addopts=""
```

Check code coverage:

```bash
docker compose exec web-a pytest --cov --cov-report=term-missing
docker compose exec web-b pytest -o addopts="" --cov --cov-report=term-missing
```

The minimum required code coverage is 70%.