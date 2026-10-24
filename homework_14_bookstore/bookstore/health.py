from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_safe


@require_safe
def health_check(request):
    """Return service status: database and cache availability."""

    checks = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = 'ok'
    except Exception:
        checks['database'] = 'error'

    try:
        cache.set('health:ping', 'pong', timeout=10)
        checks['cache'] = 'ok' if cache.get('health:ping') == 'pong' else 'error'
    except Exception:
        checks['cache'] = 'error'

    healthy = all(value == 'ok' for value in checks.values())

    return JsonResponse(
        {'status': 'ok' if healthy else 'error', **checks},
        status=200 if healthy else 503,
    )
