# Stock Transfer Management System — Technical Design

## Objective
Web application to manage stock transfers between warehouses: create warehouses, maintain
stock levels, raise transfer requests, manage transfer status, and view transfer history.

## Architecture

Single deployable service, single PostgreSQL database, single repo.

- **Django** — owns the data model (`models.py`, migrations) and the Django admin panel
  (`/admin`) for direct CRUD on warehouses, products, stock, and transfers.
- **FastAPI** — exposes the REST API (`/api/*`) and serves a minimal static frontend
  (`/`). Imports Django's ORM models directly (via `django.setup()`) — no duplicate
  schema/SQLAlchemy layer.
- Django's admin WSGI app is mounted inside the FastAPI ASGI app (via `WSGIMiddleware`),
  so a single `uvicorn` process serves everything: frontend on `/`, API on `/api`, admin
  on `/admin`.

```
┌─────────────────────────────────────────┐
│              uvicorn (ASGI)              │
│  ┌───────────┐  ┌────────┐  ┌─────────┐  │
│  │  FastAPI  │  │ Static │  │ Django  │  │
│  │  /api/*   │  │  UI /  │  │ /admin  │  │
│  └─────┬─────┘  └────────┘  └────┬────┘  │
│        └──────────┬───────────────┘      │
│              Django ORM                  │
└────────────────────┬──────────────────────┘
                      │
                 PostgreSQL
```

## Data model

- **Product**: id, name, sku (unique)
- **Warehouse**: id, name, location
- **WarehouseStock**: warehouse (FK), product (FK), quantity — unique together (warehouse, product)
- **Transfer**: id, source_warehouse (FK), destination_warehouse (FK), product (FK),
  quantity, status (`PENDING` / `COMPLETED` / `CANCELLED`), created_at, updated_at

## Business rules

- Transfer creation: source ≠ destination; quantity > 0; source warehouse must have
  sufficient stock of the product. Stock is **not** moved yet — transfer starts `PENDING`.
- Status → `COMPLETED`: inside one DB transaction, deduct quantity from source
  `WarehouseStock`, add to destination `WarehouseStock` (create the row if absent).
  Re-validates source stock at completion time to guard against race conditions.
- Status → `CANCELLED`: no stock change.
- Terminal states (`COMPLETED`, `CANCELLED`) cannot transition further.

## API (`/api`)

| Method | Path                        | Description                                  |
|--------|------------------------------|-----------------------------------------------|
| POST   | /api/warehouses              | Create warehouse                              |
| GET    | /api/warehouses              | List warehouses                               |
| GET    | /api/warehouses/{id}/stock   | Stock levels for a warehouse                  |
| POST   | /api/products                | Create product                                |
| GET    | /api/products                | List products                                 |
| POST   | /api/transfers                | Create transfer request                       |
| GET    | /api/transfers                | List transfers (filter by status, warehouse)  |
| GET    | /api/transfers/{id}           | Transfer detail                               |
| PATCH  | /api/transfers/{id}/status    | Transition status (COMPLETED / CANCELLED)     |

## Frontend

Minimal static HTML/CSS/vanilla JS, served by FastAPI `StaticFiles`, calling the API:

1. **Dashboard** (`/`) — warehouses with stock per product
2. **New Transfer** — form to create a transfer request
3. **Transfers** — history table with status + Complete/Cancel actions on PENDING rows

## Stack

- Django (ORM, admin, migrations)
- FastAPI + Pydantic (API layer)
- PostgreSQL
- uvicorn (ASGI server)
- pytest for tests
- Plain HTML/CSS/JS frontend (no build step)

## Deployment

Render — one web service (Docker), one managed PostgreSQL instance. `Dockerfile` runs
Django migrations then starts uvicorn. Config via environment variables (`DATABASE_URL`,
`DJANGO_SECRET_KEY`, `DEBUG`).

## Repo layout

```
stms/
  config/                # Django settings, WSGI/ASGI glue
  core/                  # Django app: models, admin
  api/                   # FastAPI routers, schemas, business logic
  static/                # frontend (index.html, transfers.html, app.js, style.css)
  tests/
  manage.py
  main.py                # FastAPI app entrypoint, mounts Django admin + static
  Dockerfile
  requirements.txt
  README.md
```
