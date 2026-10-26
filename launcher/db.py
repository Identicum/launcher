"""Database schema and engine.

The tables mirror the schema Hibernate generated for the Java version of the launcher,
so an existing database can be reused as-is.
"""

import logging
import os

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Identity,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    literal,
    select,
)
from sqlalchemy.engine import URL, Engine
from sqlalchemy.schema import CreateTable

logger = logging.getLogger(__name__)

# SQLite only autoincrements INTEGER PRIMARY KEY columns
Id = BigInteger().with_variant(Integer, "sqlite")

metadata = MetaData()

link = Table(
    "link",
    metadata,
    Column("id", Id, Identity(), primary_key=True),
    Column("color", String(255)),
    Column("display", String(255)),
    Column("icon", String(255)),
    Column("target", String(255)),
    Column("type", String(255)),
)

role = Table(
    "role",
    metadata,
    Column("id", Id, Identity(), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("link_id", Id, ForeignKey("link.id")),
)


def make_engine(url: URL) -> Engine:
    if url.get_backend_name() == "sqlite" and url.database:
        os.makedirs(os.path.dirname(os.path.abspath(url.database)), exist_ok=True)
    return create_engine(url, pool_pre_ping=True)


def create_tables(engine: Engine) -> None:
    """Create missing tables. Existing tables are never altered."""
    metadata.create_all(engine, checkfirst=True)


def check(engine: Engine) -> None:
    with engine.connect() as conn:
        conn.execute(select(literal(1)))


def ddl(dialect_name: str) -> str:
    """CREATE TABLE statements for a dialect, for DBAs who don't let the app create tables."""
    from sqlalchemy.dialects import registry

    dialect = registry.load(dialect_name)()
    return "\n".join(f"{str(CreateTable(t).compile(dialect=dialect)).strip()};\n" for t in metadata.sorted_tables)
