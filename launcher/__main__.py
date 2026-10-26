"""Command line: `launcher serve` (default) and maintenance commands."""

import argparse
import json
import logging
import os
import sys

from . import dataio, db
from .config import DRIVERS, ConfigError, Settings, as_bool, build_db_url


def _engine():
    engine = db.make_engine(build_db_url(os.environ))
    if as_bool(os.environ.get("DB_AUTO_CREATE", "true")):
        db.create_tables(engine)
    return engine


def serve(args) -> None:
    import uvicorn

    from .app import create_app

    settings = Settings.from_env()
    uvicorn.run(
        create_app(settings),
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8080")),
        log_config=None,
        proxy_headers=True,
        forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS", "*"),
    )


def import_file(args) -> None:
    with open(args.file, "rb") as f:
        items = dataio.parse(f.read())
    with _engine().begin() as conn:
        print(json.dumps(dataio.import_links(conn, items, dataio.ImportMode(args.mode))))


def export_file(args) -> None:
    with _engine().connect() as conn:
        document = json.dumps(dataio.export_document(conn), indent=2, ensure_ascii=False)
    if args.file == "-":
        print(document)
    else:
        with open(args.file, "w", encoding="utf-8") as f:
            f.write(document + "\n")


def normalize_roles(args) -> None:
    with _engine().begin() as conn:
        changes = dataio.normalize_roles(conn, dry_run=args.dry_run)
    for link_id, old, new in changes:
        print(f"link {link_id}: {old!r} -> {new!r}")
    print(f"{len(changes)} role(s) {'would change' if args.dry_run else 'changed'}")


def print_ddl(args) -> None:
    print(db.ddl(args.dialect))


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="launcher", description="Application launcher hosted behind IPAx")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("serve", help="run the web server (default)").set_defaults(func=serve)

    cmd = commands.add_parser("import", help="import links from a JSON file")
    cmd.add_argument("file")
    cmd.add_argument("--mode", choices=[m.value for m in dataio.ImportMode], default="skip")
    cmd.set_defaults(func=import_file)

    cmd = commands.add_parser("export", help="export links to a JSON file")
    cmd.add_argument("file", nargs="?", default="-", help="output file (default: stdout)")
    cmd.set_defaults(func=export_file)

    cmd = commands.add_parser("normalize-roles", help="convert DN role names (CN=App01,OU=...) to plain names (App01)")
    cmd.add_argument("--dry-run", action="store_true", help="only show what would change")
    cmd.set_defaults(func=normalize_roles)

    cmd = commands.add_parser("ddl", help="print CREATE TABLE statements for a database type")
    cmd.add_argument("dialect", choices=list(DRIVERS))
    cmd.set_defaults(func=print_ddl)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    try:
        (getattr(args, "func", None) or serve)(args)
    except (ConfigError, dataio.ImportFileError) as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
