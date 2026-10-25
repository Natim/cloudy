"""Structured API errors."""

from typing import Any

from ninja.errors import HttpError


class ApiHttpError(HttpError):
    def __init__(
        self,
        status_code: int,
        detail: str,
        *,
        code: str | None = None,
        errors: dict[str, Any] | None = None,
    ):
        super().__init__(status_code, detail)
        self.api_code = code
        self.api_errors = errors or {}


def plan_required(detail: str = "First Class plan required for additional logbooks") -> ApiHttpError:
    return ApiHttpError(403, detail, code="plan_required")


def storage_quota(detail: str = "Insufficient storage quota") -> ApiHttpError:
    return ApiHttpError(403, detail, code="storage_quota")


def invalid_payload(detail: str, errors: dict[str, Any] | None = None) -> ApiHttpError:
    return ApiHttpError(400, detail, code="invalid", errors=errors or {})


def api_error_response(request, exc: ApiHttpError):
    from ninja.responses import Response

    body: dict[str, Any] = {"detail": exc.message, "code": exc.api_code or "error"}
    if exc.api_errors:
        body["errors"] = exc.api_errors
    return Response(body, status=exc.status_code)
