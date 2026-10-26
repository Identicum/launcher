"""FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, RedirectResponse

from . import dataio, db, links
from .auth import SameOriginMiddleware, User, admin_user, current_user
from .config import Settings

logger = logging.getLogger(__name__)


def load_initial_data(settings: Settings, engine) -> None:
    """Seed an empty database from INITIAL_DATA_FILE, like the Java version did with data.json."""
    with engine.begin() as conn:
        if links.count_links(conn):
            logger.debug("Database already has links. Skipping initial data.")
            return
        path = settings.initial_data_file
        if not os.path.isfile(path):
            logger.info("Database is empty and %s was not found. Starting without links.", path)
            return
        with open(path, "rb") as f:
            result = dataio.import_links(conn, dataio.parse(f.read()))
        logger.info("Loaded initial data from %s: %s", path, result)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = db.make_engine(settings.db_url)
        logger.info("Using %s database", settings.db_url.get_backend_name())
        if settings.db_auto_create:
            db.create_tables(engine)
        load_initial_data(settings, engine)
        app.state.engine = engine
        yield
        engine.dispose()

    app = FastAPI(title=settings.app_title, lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.add_middleware(SameOriginMiddleware)

    def get_engine(request: Request):
        return request.app.state.engine

    @app.get("/health", include_in_schema=False)
    def health(engine=Depends(get_engine)):
        try:
            db.check(engine)
        except Exception:
            logger.exception("Health check failed")
            return JSONResponse({"status": "DOWN"}, status_code=503)
        return {"status": "UP"}

    @app.get("/logout")
    def logout():
        return RedirectResponse(settings.logout_url)

    @app.get("/api/me")
    def me(user: User = Depends(current_user)):
        return {"username": user.username, "roles": list(user.roles), "admin": user.is_admin}

    @app.get("/api/links")
    def my_links(query: str = "", user: User = Depends(current_user), engine=Depends(get_engine)):
        with engine.connect() as conn:
            return links.visible_links(conn, user.roles, settings.public_role, query)

    @app.get("/links/search")
    def search(query: str = "", user: User = Depends(current_user), engine=Depends(get_engine)):
        """Autocomplete endpoint of the Java version: [{display, color, icon, target, type}]."""
        with engine.connect() as conn:
            found = links.visible_links(conn, user.roles, settings.public_role, query)
        return [{key: item[key] for key in ("display", "color", "icon", "target", "type")} for item in found]

    # ---- administration ----

    def admin_view(item: dict) -> dict:
        return {**item, "roles": [r["name"] for r in item["roles"]]}

    @app.get("/api/admin/links", dependencies=[Depends(admin_user)])
    def admin_list(engine=Depends(get_engine)):
        with engine.connect() as conn:
            return [admin_view(item) for item in links.all_links(conn)]

    @app.post("/api/admin/links", status_code=201, dependencies=[Depends(admin_user)])
    def admin_create(data: links.LinkIn, engine=Depends(get_engine)):
        with engine.begin() as conn:
            return admin_view(links.get_link(conn, links.create_link(conn, data)))

    @app.get("/api/admin/links/{link_id}", dependencies=[Depends(admin_user)])
    def admin_get(link_id: int, engine=Depends(get_engine)):
        with engine.connect() as conn:
            item = links.get_link(conn, link_id)
        if item is None:
            raise HTTPException(404, "Link not found")
        return admin_view(item)

    @app.put("/api/admin/links/{link_id}", dependencies=[Depends(admin_user)])
    def admin_update(link_id: int, data: links.LinkIn, engine=Depends(get_engine)):
        with engine.begin() as conn:
            if not links.update_link(conn, link_id, data):
                raise HTTPException(404, "Link not found")
            return admin_view(links.get_link(conn, link_id))

    @app.delete("/api/admin/links/{link_id}", status_code=204, dependencies=[Depends(admin_user)])
    def admin_delete(link_id: int, engine=Depends(get_engine)):
        with engine.begin() as conn:
            if not links.delete_link(conn, link_id):
                raise HTTPException(404, "Link not found")

    @app.get("/admin/data/export", dependencies=[Depends(admin_user)])
    def export(engine=Depends(get_engine)):
        with engine.connect() as conn:
            document = dataio.export_document(conn)
        filename = f"launcher-{date.today():%Y%m%d}.json"
        return JSONResponse(document, headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    @app.post("/admin/data/import", dependencies=[Depends(admin_user)])
    async def import_data(request: Request, mode: dataio.ImportMode | None = None, engine=Depends(get_engine)):
        """Accepts the multipart upload of the Java version (field importFile) or a raw JSON body.

        The mode (skip, update, replace) comes from the query string or a "mode" form field.
        """
        if request.headers.get("content-type", "").startswith("multipart/form-data"):
            form = await request.form()
            upload = form.get("importFile")
            if upload is None or isinstance(upload, str):
                raise HTTPException(400, "Missing importFile")
            content = await upload.read()
            if mode is None and form.get("mode"):
                try:
                    mode = dataio.ImportMode(form["mode"])
                except ValueError:
                    raise HTTPException(400, f"mode must be one of {', '.join(m.value for m in dataio.ImportMode)}")
        else:
            content = await request.body()
        try:
            items = dataio.parse(content)
        except dataio.ImportFileError as e:
            return JSONResponse({"status": "error", "errors": e.errors}, status_code=400)
        def run():
            with engine.begin() as conn:
                return dataio.import_links(conn, items, mode or dataio.ImportMode.skip)

        return await run_in_threadpool(run)

    return app
