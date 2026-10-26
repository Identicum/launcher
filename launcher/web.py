"""HTML pages: templates, static files, error pages and security headers."""

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from .auth import user_from_headers
from .links import COLOR_PATTERN, UNSAFE_SCHEMES

BASE = Path(__file__).parent
API_PREFIXES = ("/api/", "/admin/data/", "/links/", "/health", "/static/")
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https: http:; font-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'"
)
ERRORS = {
    401: ("fa-user-lock", "Not signed in", "The launcher must be accessed through IPAx, which signs you in."),
    403: ("fa-lock", "Access denied", "This page is for launcher administrators only."),
    404: ("fa-compass", "Page not found", "The page you were looking for doesn't exist."),
}

try:
    VERSION = version("launcher")
except PackageNotFoundError:
    VERSION = "dev"


def safe_url(value) -> str:
    """Link targets saved before validation existed may still hold a script URL."""
    value = value or ""
    return "#" if value.strip().lower().replace(" ", "").startswith(UNSAFE_SCHEMES) else value


def safe_color(value) -> str:
    return value if value and COLOR_PATTERN.match(value) else "var(--tile-default)"


def css_value(value) -> str:
    """Keep STYLE_* settings inside their CSS declaration."""
    return re.sub(r"[<>{};]", "", value or "")


def setup(app: FastAPI) -> Jinja2Templates:
    templates = Jinja2Templates(directory=BASE / "templates")
    templates.env.filters.update(safe_url=safe_url, safe_color=safe_color, css_value=css_value)
    templates.env.globals["static"] = lambda path: f"/static/{path}?v={VERSION}"
    app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

    def wants_html(request: Request) -> bool:
        return (
            request.method == "GET"
            and not request.url.path.startswith(API_PREFIXES)
            and "text/html" in request.headers.get("accept", "")
        )

    @app.exception_handler(StarletteHTTPException)
    async def error_page(request: Request, exc: StarletteHTTPException):
        if not wants_html(request) or exc.status_code not in ERRORS:
            return await http_exception_handler(request, exc)
        icon, heading, message = ERRORS[exc.status_code]
        settings = request.app.state.settings
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "settings": settings,
                "user": user_from_headers(request.headers, settings.admin_role),
                "status": exc.status_code,
                "icon": icon,
                "heading": heading,
                "message": message,
            },
            status_code=exc.status_code,
        )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if response.headers.get("content-type", "").startswith("text/html"):
            response.headers.setdefault("Content-Security-Policy", CSP)
        return response

    return templates
