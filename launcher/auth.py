"""Authentication delegated to IPAx.

IPAx authenticates the user and forwards:
  IPAx-USERNAME: the user name
  IPAx-ROLES:    the user's role (group) names, separated by "|"
The launcher must only be reachable through IPAx, or these headers could be forged.
"""

from dataclasses import dataclass
from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

USERNAME_HEADER = "IPAx-USERNAME"
ROLES_HEADER = "IPAx-ROLES"
ROLE_SEPARATOR = "|"
SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


@dataclass(frozen=True)
class User:
    username: str
    roles: tuple[str, ...]
    is_admin: bool


def user_from_headers(headers, admin_role: str) -> User | None:
    username = (headers.get(USERNAME_HEADER) or "").strip()
    if not username:
        return None
    roles = tuple(dict.fromkeys(r.strip() for r in (headers.get(ROLES_HEADER) or "").split(ROLE_SEPARATOR) if r.strip()))
    return User(username=username, roles=roles, is_admin=admin_role in roles)


def current_user(request: Request) -> User:
    user = user_from_headers(request.headers, request.app.state.settings.admin_role)
    if user is None:
        raise HTTPException(401, f"Missing {USERNAME_HEADER} header: the launcher must be accessed through IPAx")
    return user


def admin_user(request: Request) -> User:
    user = current_user(request)
    if not user.is_admin:
        raise HTTPException(403, "Launcher administrators only")
    return user


class SameOriginMiddleware:
    """Reject cross-site write requests (CSRF), using the headers browsers add to them.

    Requests without these headers (curl, scripts) are allowed.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and scope["method"] not in SAFE_METHODS and not self._same_origin(Headers(scope=scope)):
            await JSONResponse({"detail": "Cross-site request rejected"}, status_code=403)(scope, receive, send)
            return
        await self.app(scope, receive, send)

    @staticmethod
    def _same_origin(headers: Headers) -> bool:
        if headers.get("sec-fetch-site", "same-origin") not in ("same-origin", "none"):
            return False
        origin = headers.get("origin")
        if origin is None:
            return True
        return urlsplit(origin).netloc == headers.get("host")
