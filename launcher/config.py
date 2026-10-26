"""Configuration, read from environment variables."""

import os
from dataclasses import dataclass

from sqlalchemy.engine import URL, make_url

DRIVERS = {
    "sqlite": "sqlite",
    "postgresql": "postgresql+psycopg",
    "oracle": "oracle+oracledb",
    "mysql": "mysql+pymysql",
}
DEFAULT_PORTS = {"postgresql": 5432, "oracle": 1521, "mysql": 3306}


class ConfigError(Exception):
    pass


def as_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


def build_db_url(env) -> URL:
    """DB_URL wins; otherwise assemble the URL from DB_TYPE, DB_HOST, ... (no escaping needed)."""
    if env.get("DB_URL"):
        return make_url(env["DB_URL"])
    db_type = env.get("DB_TYPE", "sqlite").lower()
    if db_type not in DRIVERS:
        raise ConfigError(f"DB_TYPE must be one of {', '.join(DRIVERS)} (got '{db_type}')")
    if db_type == "sqlite":
        data_dir = env.get("DATA_DIR", "/data")
        return URL.create("sqlite", database=env.get("DB_NAME") or os.path.join(data_dir, "launcher.db"))
    for required in ("DB_HOST", "DB_NAME", "DB_USER"):
        if not env.get(required):
            raise ConfigError(f"{required} is required when DB_TYPE={db_type}")
    port = int(env.get("DB_PORT") or DEFAULT_PORTS[db_type])
    common = dict(
        drivername=DRIVERS[db_type],
        username=env["DB_USER"],
        password=env.get("DB_PASSWORD"),
        host=env["DB_HOST"],
        port=port,
    )
    if db_type == "oracle":
        # DB_NAME is the Oracle service name
        return URL.create(**common, query={"service_name": env["DB_NAME"]})
    return URL.create(**common, database=env["DB_NAME"])


@dataclass(frozen=True)
class Settings:
    db_url: URL
    admin_role: str
    public_role: str = "PUBLIC"
    db_auto_create: bool = True
    initial_data_file: str = "/data/data.json"
    logout_url: str = "/private/logout"
    log_level: str = "INFO"
    app_title: str = "App Launcher"
    style_background: str = ""
    style_background_size: str = ""

    @classmethod
    def from_env(cls, env=None) -> "Settings":
        env = os.environ if env is None else env
        admin_role = env.get("ADMIN_ROLE", "").strip()
        if not admin_role:
            raise ConfigError("ADMIN_ROLE is required (the IPAx role that grants launcher administration)")
        data_dir = env.get("DATA_DIR", "/data")
        return cls(
            db_url=build_db_url(env),
            admin_role=admin_role,
            public_role=env.get("PUBLIC_ROLE", "PUBLIC").strip() or "PUBLIC",
            db_auto_create=as_bool(env.get("DB_AUTO_CREATE", "true")),
            initial_data_file=env.get("INITIAL_DATA_FILE") or os.path.join(data_dir, "data.json"),
            logout_url=env.get("LOGOUT_URL", "/private/logout"),
            log_level=env.get("LOG_LEVEL", "INFO").upper(),
            app_title=env.get("APP_TITLE", "App Launcher"),
            style_background=env.get("STYLE_BACKGROUND", ""),
            style_background_size=env.get("STYLE_BACKGROUND_SIZE", ""),
        )
