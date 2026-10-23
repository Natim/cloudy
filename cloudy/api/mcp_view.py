"""Django view bridging WSGI requests to the MCP Streamable HTTP ASGI app."""

from asgiref.sync import async_to_sync
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .auth import authenticate_bearer, set_api_user
from .mcp_server import mcp

_starlette_app = None


def _get_asgi_app():
    global _starlette_app
    if _starlette_app is None:
        _starlette_app = mcp.streamable_http_app(
            streamable_http_path="/",
            stateless_http=True,
            json_response=True,
        )
    return _starlette_app


def _build_scope(request, path: str) -> dict:
    headers = []
    for key, value in request.headers.items():
        headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "HTTP/1.1",
        "method": request.method,
        "scheme": "https" if request.is_secure() else "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": request.META.get("QUERY_STRING", "").encode("utf-8"),
        "headers": headers,
        "client": None,
        "server": None,
    }


@csrf_exempt
@require_http_methods(["GET", "POST", "DELETE"])
def mcp_endpoint(request):
    user = authenticate_bearer(request)
    if user is None:
        return HttpResponseForbidden("Invalid or missing bearer token")
    set_api_user(user)

    body = request.body
    response_status = 500
    response_headers: list[tuple[bytes, bytes]] = []
    response_body = b""

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        nonlocal response_status, response_headers, response_body
        if message["type"] == "http.response.start":
            response_status = message["status"]
            response_headers = message.get("headers", [])
        elif message["type"] == "http.response.body":
            response_body += message.get("body", b"")

    scope = _build_scope(request, "/")
    async_to_sync(_get_asgi_app())(scope, receive, send)

    django_response = HttpResponse(response_body, status=response_status)
    for header, value in response_headers:
        django_response[header.decode("latin-1")] = value.decode("latin-1")
    return django_response
