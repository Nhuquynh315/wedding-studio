from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_PROBLEM_CONTENT_TYPE = "application/problem+json"

_STATUS_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    413: "Payload Too Large",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}


def _problem_response(
    status_code: int,
    detail: Any = None,
    instance: str | None = None,
    title: str | None = None,
    extensions: dict | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": title or _STATUS_TITLES.get(status_code, "Error"),
        "status": status_code,
    }
    if instance is not None:
        body["instance"] = instance

    if isinstance(detail, str):
        body["detail"] = detail
    elif isinstance(detail, dict):
        # Lift "message" key into RFC 7807 "detail" field; promote all
        # other keys (e.g. row_errors) to top-level extension fields.
        if "message" in detail:
            body["detail"] = detail["message"]
        for key, value in detail.items():
            if key != "message":
                body[key] = value
    elif detail is not None:
        body["detail"] = str(detail)

    if extensions:
        body.update(extensions)

    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type=_PROBLEM_CONTENT_TYPE,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    headers = exc.headers if hasattr(exc, "headers") else None
    response = _problem_response(
        status_code=exc.status_code,
        detail=exc.detail,
        instance=str(request.url.path),
    )
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]} for err in exc.errors()
    ]
    return _problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="One or more fields failed validation",
        instance=str(request.url.path),
        extensions={"errors": errors},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import sys
    import traceback

    print(f"Unhandled exception: {exc}", file=sys.stderr)
    traceback.print_exc()
    return _problem_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred",
        instance=str(request.url.path),
    )


def install_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
