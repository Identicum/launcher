import pytest

from launcher.config import ConfigError, Settings, build_db_url


def test_admin_role_is_required():
    with pytest.raises(ConfigError, match="ADMIN_ROLE"):
        Settings.from_env({})


def test_defaults_to_sqlite_in_data_dir():
    settings = Settings.from_env({"ADMIN_ROLE": "Admins", "DATA_DIR": "/srv/launcher"})
    assert settings.db_url.render_as_string() == "sqlite:////srv/launcher/launcher.db"
    assert settings.initial_data_file == "/srv/launcher/data.json"
    assert settings.public_role == "PUBLIC"
    assert settings.logout_url == "/private/logout"


def test_db_url_wins():
    url = build_db_url({"DB_URL": "postgresql+psycopg://u:p@h/d", "DB_TYPE": "oracle"})
    assert url.drivername == "postgresql+psycopg"


def test_split_variables_need_no_escaping():
    url = build_db_url(
        {"DB_TYPE": "postgresql", "DB_HOST": "db", "DB_NAME": "launcherdb", "DB_USER": "u", "DB_PASSWORD": "p@ss:/w#rd"}
    )
    assert (url.drivername, url.host, url.port, url.database, url.password) == (
        "postgresql+psycopg", "db", 5432, "launcherdb", "p@ss:/w#rd"
    )


def test_oracle_uses_service_name():
    url = build_db_url({"DB_TYPE": "oracle", "DB_HOST": "ora", "DB_NAME": "FREEPDB1", "DB_USER": "u"})
    assert (url.drivername, url.port, url.database, url.query["service_name"]) == (
        "oracle+oracledb", 1521, None, "FREEPDB1"
    )


def test_mysql_driver():
    assert build_db_url({"DB_TYPE": "mysql", "DB_HOST": "h", "DB_NAME": "d", "DB_USER": "u"}).drivername == "mysql+pymysql"


@pytest.mark.parametrize("env", [{"DB_TYPE": "mssql"}, {"DB_TYPE": "postgresql", "DB_NAME": "d", "DB_USER": "u"}])
def test_invalid_db_config(env):
    with pytest.raises(ConfigError):
        build_db_url(env)
