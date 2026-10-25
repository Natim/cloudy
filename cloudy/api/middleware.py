from .auth import set_api_user


class ClearApiUserMiddleware:
    """Reset MCP/API context user after each request (WSGI thread reuse)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        finally:
            set_api_user(None)
