"""Import/export in the JSON format of the Java launcher, and role-name migration.

Format: {"links": [{"id", "icon", "color", "target", "type", "display", "roles": [{"id", "name"}]}]}
Ids are written on export and ignored on import.
"""

import json
import logging
import re
from enum import Enum

from pydantic import ValidationError
from sqlalchemy import delete, select, update
from sqlalchemy.engine import Connection

from . import links
from .db import role

logger = logging.getLogger(__name__)

DN_PATTERN = re.compile(r"^\s*[A-Za-z][\w.-]*\s*=")


class ImportMode(str, Enum):
    skip = "skip"  # keep links whose target already exists (behaviour of the Java version)
    update = "update"  # overwrite links whose target already exists, including their roles
    replace = "replace"  # delete every link first


class ImportFileError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def role_name(value: str) -> str:
    """'CN=App01,OU=groups,DC=sherpa,DC=com' -> 'App01', the same way IPAx builds IPAx-ROLES."""
    if not DN_PATTERN.match(value):
        return value.strip()
    return value.split(",", 1)[0].split("=", 2)[1].strip()


def _role_names(raw) -> list[str]:
    names = []
    for item in raw or []:
        name = item.get("name") if isinstance(item, dict) else item
        if not isinstance(name, str):
            raise ValueError(f"invalid role {item!r}")
        names.append(role_name(name))
    return names


def parse(content: bytes | str) -> list[links.LinkIn]:
    """Validate a whole import file; raise ImportFileError listing every problem."""
    try:
        document = json.loads(content)
    except (ValueError, UnicodeDecodeError) as e:
        raise ImportFileError([f"not valid JSON: {e}"])
    if not isinstance(document, dict) or not isinstance(document.get("links"), list):
        raise ImportFileError(['expected an object with a "links" list'])

    parsed, errors = [], []
    for index, raw in enumerate(document["links"]):
        label = f"links[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{label}: expected an object")
            continue
        label = f"{label} ({raw.get('display') or raw.get('target') or 'no display'})"
        try:
            fields = {key: raw.get(key) for key in ("display", "target", "icon", "color") if raw.get(key) is not None}
            fields["type"] = raw.get("type") or "html"
            fields["roles"] = _role_names(raw.get("roles"))
            parsed.append(links.LinkIn(**fields))
        except ValidationError as e:
            errors += [f"{label}: {'.'.join(map(str, err['loc']))} {err['msg']}" for err in e.errors()]
        except ValueError as e:
            errors.append(f"{label}: {e}")
    if errors:
        raise ImportFileError(errors)
    return parsed


def import_links(conn: Connection, items: list[links.LinkIn], mode: ImportMode = ImportMode.skip) -> dict:
    """Run inside a transaction: on error nothing is changed."""
    result = {"status": "ok", "mode": mode.value, "created": 0, "updated": 0, "skipped": 0, "deleted": 0}
    if mode == ImportMode.replace:
        result["deleted"] = links.delete_all(conn)
    for item in items:
        existing = links.ids_by_target(conn, item.target)
        if not existing:
            links.create_link(conn, item)
            result["created"] += 1
        elif mode == ImportMode.update:
            for link_id in existing:
                links.update_link(conn, link_id, item)
            result["updated"] += len(existing)
        else:
            logger.info("Link with target '%s' already exists. Skipping.", item.target)
            result["skipped"] += 1
    logger.info("Import finished: %s", result)
    return result


def export_document(conn: Connection) -> dict:
    return {
        "links": [
            {
                "id": item["id"],
                "icon": item["icon"],
                "color": item["color"],
                "target": item["target"],
                "type": item["type"],
                "display": item["display"],
                "roles": item["roles"],
            }
            for item in links.export_links(conn)
        ]
    }


def normalize_roles(conn: Connection, dry_run: bool = False) -> list[tuple[int, str, str]]:
    """Rewrite DN role names to the plain names IPAx sends, dropping roles a link would then have twice.

    Returns (link_id, old, new) per changed or removed role.
    """
    changes = []
    seen: dict[int, set[str]] = {}
    for row in conn.execute(select(role.c.id, role.c.name, role.c.link_id).order_by(role.c.id)):
        new = role_name(row.name)
        names = seen.setdefault(row.link_id, set())
        if new in names:  # the link already has this role: drop the duplicate
            changes.append((row.link_id, row.name, new))
            if not dry_run:
                conn.execute(delete(role).where(role.c.id == row.id))
        elif new != row.name:
            changes.append((row.link_id, row.name, new))
            if not dry_run:
                conn.execute(update(role).where(role.c.id == row.id).values(name=new))
        names.add(new)
    return changes
