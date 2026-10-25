from django.conf import settings
from django.http import HttpResponse

from .auth import set_api_user


class ApiCorsMiddleware:
    """CORS for the mobile /api/v1 JSON API (separate PWA origin)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/v1/"):
            return self.get_response(request)

        origin = request.META.get("HTTP_ORIGIN", "")
        allowed = getattr(settings, "CORS_ALLOWED_ORIGINS", frozenset())

        if request.method == "OPTIONS":
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        if origin and origin in allowed:
            response["Access-Control-Allow-Origin"] = origin
            response["Vary"] = "Origin"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response["Access-Control-Max-Age"] = "86400"

        return response


class ClearApiUserMiddleware:
    """Reset MCP/API context user after each request (WSGI thread reuse)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        finally:
            set_api_user(None)
