import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from a2wsgi import WSGIMiddleware  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.responses import RedirectResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from api.routers import products, transfers, warehouses  # noqa: E402
from config.settings import STATIC_ROOT  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Stock Transfer Management System")

app.include_router(warehouses.router)
app.include_router(products.router)
app.include_router(transfers.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


django_wsgi_app = get_wsgi_application()
app.mount("/admin", WSGIMiddleware(django_wsgi_app))

if STATIC_ROOT.exists():
    app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="django-static")


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse(url="/app/")


app.mount("/app", StaticFiles(directory=BASE_DIR / "frontend", html=True), name="frontend")
