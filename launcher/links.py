"""Link and role persistence."""

import re
from typing import Iterable

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Connection

from .db import link, role

UNSAFE_SCHEMES = ("javascript:", "data:", "vbscript:")
COLOR_PATTERN = re.compile(r"^[#\w\s(),.%-]*$")


class LinkIn(BaseModel):
    """A link as written by admins or read from an import file."""

    display: str = Field(min_length=1, max_length=255)
    target: str = Field(min_length=1, max_length=255)
    icon: str | None = Field(default=None, max_length=255)
    color: str | None = Field(default=None, max_length=255)
    type: str | None = Field(default="html", max_length=255)
    roles: list[str] = []

    @field_validator("display", "target", "icon", "color", "type", mode="before")
    @classmethod
    def strip(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("icon", "color", "type")
    @classmethod
    def empty_to_none(cls, value):
        return value or None

    @field_validator("target")
    @classmethod
    def safe_target(cls, value):
        if value.lower().replace(" ", "").startswith(UNSAFE_SCHEMES):
            raise ValueError("target must not use a javascript:, data: or vbscript: URL")
        return value

    @field_validator("color")
    @classmethod
    def safe_color(cls, value):
        if value and not COLOR_PATTERN.match(value):
            raise ValueError("color must be a CSS color such as #ED5151")
        return value

    @field_validator("roles")
    @classmethod
    def clean_roles(cls, value):
        names = []
        for name in value:
            name = name.strip()
            if len(name) > 255:
                raise ValueError("role names must be at most 255 characters")
            if name and name not in names:
                names.append(name)
        return names


def _columns(data: LinkIn) -> dict:
    return dict(display=data.display, target=data.target, icon=data.icon, color=data.color, type=data.type)


def _roles_by_link(conn: Connection, link_ids: list[int]) -> dict[int, list[dict]]:
    result: dict[int, list[dict]] = {link_id: [] for link_id in link_ids}
    if not link_ids:
        return result
    rows = conn.execute(
        select(role.c.id, role.c.name, role.c.link_id).where(role.c.link_id.in_(link_ids)).order_by(role.c.name)
    )
    for row in rows:
        result[row.link_id].append({"id": row.id, "name": row.name})
    return result


def _with_roles(conn: Connection, rows) -> list[dict]:
    links = [dict(row._mapping) for row in rows]
    roles = _roles_by_link(conn, [item["id"] for item in links])
    for item in links:
        item["roles"] = roles[item["id"]]
    return links


def visible_links(conn: Connection, user_roles: Iterable[str], public_role: str, query: str = "") -> list[dict]:
    """Links granted to any of the user's roles, or to the public role.

    Role matching is case-sensitive. Some databases (MySQL) compare case-insensitively,
    so the database narrows the candidates and the exact comparison is done here.
    """
    names = {public_role, *user_roles}
    candidates = select(role.c.link_id, role.c.name).where(role.c.name.in_(names))
    granted = {row.link_id for row in conn.execute(candidates) if row.name in names}
    stmt = select(link).where(link.c.id.in_(select(role.c.link_id).where(role.c.name.in_(names))))
    if query:
        stmt = stmt.where(func.lower(link.c.display).contains(query.lower(), autoescape=True))
    rows = conn.execute(stmt.order_by(func.lower(link.c.display), link.c.id))
    return [dict(row._mapping) for row in rows if row.id in granted]


def all_links(conn: Connection) -> list[dict]:
    return _with_roles(conn, conn.execute(select(link).order_by(func.lower(link.c.display), link.c.id)))


def export_links(conn: Connection) -> list[dict]:
    return _with_roles(conn, conn.execute(select(link).order_by(link.c.id)))


def get_link(conn: Connection, link_id: int) -> dict | None:
    links = _with_roles(conn, conn.execute(select(link).where(link.c.id == link_id)))
    return links[0] if links else None


def ids_by_target(conn: Connection, target: str) -> list[int]:
    rows = conn.execute(select(link.c.id, link.c.target).where(link.c.target == target).order_by(link.c.id))
    return [row.id for row in rows if row.target == target]  # exact match, also on case-insensitive databases


def count_links(conn: Connection) -> int:
    return conn.scalar(select(func.count()).select_from(link))


def _set_roles(conn: Connection, link_id: int, names: list[str]) -> None:
    conn.execute(delete(role).where(role.c.link_id == link_id))
    for name in names:
        conn.execute(insert(role).values(name=name, link_id=link_id))


def create_link(conn: Connection, data: LinkIn) -> int:
    link_id = conn.execute(insert(link).values(**_columns(data))).inserted_primary_key[0]
    _set_roles(conn, link_id, data.roles)
    return link_id


def update_link(conn: Connection, link_id: int, data: LinkIn) -> bool:
    if not conn.execute(update(link).where(link.c.id == link_id).values(**_columns(data))).rowcount:
        return False
    _set_roles(conn, link_id, data.roles)
    return True


def delete_link(conn: Connection, link_id: int) -> bool:
    conn.execute(delete(role).where(role.c.link_id == link_id))
    return bool(conn.execute(delete(link).where(link.c.id == link_id)).rowcount)


def delete_all(conn: Connection) -> int:
    conn.execute(delete(role))
    return conn.execute(delete(link)).rowcount
