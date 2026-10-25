from django.http import HttpRequest

from ..auth import JwtBearer

bearer_auth = JwtBearer()


def resource_location(request: HttpRequest, path: str) -> str:
    return request.build_absolute_uri(path)
