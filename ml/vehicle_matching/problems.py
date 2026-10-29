"""Problem Details responses for the recommendation API."""
from fastapi import Request
from fastapi.responses import JSONResponse


def problem(request: Request, status: int, title: str, detail: str, errors=None):
    body = {"type": "about:blank", "title": title, "status": status,
            "detail": detail, "instance": request.url.path}
    if errors:
        body["errors"] = errors
    return JSONResponse(body, status_code=status, media_type="application/problem+json")

