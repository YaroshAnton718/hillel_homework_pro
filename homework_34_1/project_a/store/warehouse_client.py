import logging
import time

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('store.warehouse_service')

TOKEN_CACHE_KEY = 'warehouse_service:access_token'
TOKEN_CACHE_TIMEOUT = 240


class WarehouseError(Exception):
    """Base error for communication with the warehouse_service service."""


class WarehouseUnavailable(WarehouseError):
    """Network problem, timeout or 5xx. Safe to retry."""


class WarehouseRejected(WarehouseError):
    """4xx response. Retrying will not help."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class WarehouseNotFound(WarehouseRejected):
    """404 response."""


class WarehouseClient:
    """REST client for ProjectB with JWT auth, token caching and error mapping."""

    def __init__(self, base_url=None, username=None, password=None, timeout=None):
        self.base_url = (base_url or settings.WAREHOUSE_API_URL).rstrip('/')
        self.username = username or settings.WAREHOUSE_SERVICE_USERNAME
        self.password = password or settings.WAREHOUSE_SERVICE_PASSWORD
        self.timeout = timeout or settings.WAREHOUSE_TIMEOUT


    def _login(self):
        url = f'{self.base_url}/token/'

        try:
            response = requests.post(
                url,
                json={'username': self.username, 'password': self.password},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.warning('Warehouse login failed: %s', exc)
            raise WarehouseUnavailable(str(exc)) from exc

        if response.status_code != 200:
            logger.error('Warehouse login returned %s', response.status_code)
            self._raise_for_status(response)
            raise WarehouseRejected('Warehouse login failed', response.status_code)

        token = response.json()['access']
        cache.set(TOKEN_CACHE_KEY, token, TOKEN_CACHE_TIMEOUT)

        return token

    def _token(self):
        return cache.get(TOKEN_CACHE_KEY) or self._login()


    def _send(self, method, path, **kwargs):
        url = f'{self.base_url}{path}'
        headers = {'Authorization': f'Bearer {self._token()}'}
        started = time.monotonic()

        try:
            response = requests.request(
                method, url, headers=headers, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:
            logger.warning('Warehouse %s %s failed: %s', method, url, exc)
            raise WarehouseUnavailable(str(exc)) from exc

        logger.info(
            'Warehouse %s %s -> %s (%.3fs)',
            method,
            url,
            response.status_code,
            time.monotonic() - started,
        )

        return response

    def _request(self, method, path, **kwargs):
        response = self._send(method, path, **kwargs)

        if response.status_code == 401:
            logger.info('Warehouse token rejected, re-authenticating')
            cache.delete(TOKEN_CACHE_KEY)
            response = self._send(method, path, **kwargs)

        self._raise_for_status(response)

        return response

    @staticmethod
    def _raise_for_status(response):
        status = response.status_code

        if status < 400:
            return

        if status >= 500:
            raise WarehouseUnavailable(f'Warehouse responded with {status}')

        if status == 404:
            raise WarehouseNotFound('Warehouse resource not found', status)

        raise WarehouseRejected(
            f'Warehouse rejected request: {status} {response.text[:200]}', status
        )


    def create_shipment(self, order):
        payload = {
            'order_id': order.pk,
            'email': order.email,
            'items': [
                {
                    'book_id': item.book_id,
                    'title': item.book.title,
                    'quantity': item.quantity,
                }
                for item in order.items.select_related('book')
            ],
        }

        return self._request('POST', '/shipments/', json=payload).json()

    def get_shipment(self, order_id):
        return self._request('GET', f'/shipments/{order_id}/').json()