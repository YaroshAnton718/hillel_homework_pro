import logging
import time


logger = logging.getLogger('store')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        user = (
            request.user.username
            if request.user.is_authenticated
            else 'Anonymous'
        )

        logger.info(
            '%s %s | user=%s | status=%s | %.3fs',
            request.method,
            request.path,
            user,
            response.status_code,
            duration,
        )

        return response