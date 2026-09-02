# Stock Transfer Management System

A web application to manage stock transfers between warehouses: create warehouses,
maintain stock levels, raise transfer requests, manage transfer status, and view
transfer history.

See [`DESIGN.md`](DESIGN.md) for the technical design.

## Stack

- **Django** — data model, migrations, admin panel (`/admin`)
- **FastAPI** — REST API (`/api`), serves the frontend
- **PostgreSQL** (SQLite for local dev by default)
- Plain HTML/CSS/JS frontend (`/app`) — no build step
- pytest — automated tests

All of it runs as a single process (`uvicorn main:app`): FastAPI mounts Django's admin
app and static files alongside its own API routes and the frontend.

## Live application

- App: https://stock-transfer-management-x9vd.onrender.com/app/
- Admin panel: https://stock-transfer-management-x9vd.onrender.com/admin/
- API docs (Swagger): https://stock-transfer-management-x9vd.onrender.com/docs

## Local setup

Requires Python 3.11+.

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # defaults to local sqlite, no edits needed

python manage.py migrate
python manage.py createsuperuser  # for /admin access (optional)
python manage.py collectstatic --noinput

uvicorn main:app --reload
```

Then open:

- Frontend: http://127.0.0.1:8000/app/
- Django admin: http://127.0.0.1:8000/admin/
- API docs: http://127.0.0.1:8000/docs

## Running tests

```bash
pytest
```

## Sample usage / test flow

Via the UI (`/app/`):

1. **Setup** tab → create two warehouses and a product.
2. **Setup** tab → "Set Stock Level" to give the source warehouse some stock of that product.
3. **New Transfer** tab → create a transfer request from the source to the destination warehouse.
4. **Transfers** tab → click **Complete** on the pending transfer.
5. **Dashboard** tab → confirm stock moved from source to destination warehouse.

Via the API (curl):

```bash
BASE=http://127.0.0.1:8000/api

# Create warehouses
WH1=$(curl -s -X POST $BASE/warehouses -H "Content-Type: application/json" \
  -d '{"name":"Warehouse A","location":"Delhi"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
WH2=$(curl -s -X POST $BASE/warehouses -H "Content-Type: application/json" \
  -d '{"name":"Warehouse B","location":"Mumbai"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

# Create a product
PID=$(curl -s -X POST $BASE/products -H "Content-Type: application/json" \
  -d '{"name":"Widget","sku":"WID-001"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

# Set stock at warehouse A
curl -s -X PUT $BASE/warehouses/$WH1/stock -H "Content-Type: application/json" \
  -d "{\"product_id\":$PID,\"quantity\":100}"

# Create a transfer request A -> B
TID=$(curl -s -X POST $BASE/transfers -H "Content-Type: application/json" \
  -d "{\"source_warehouse_id\":$WH1,\"destination_warehouse_id\":$WH2,\"product_id\":$PID,\"quantity\":40}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

# Complete the transfer (moves stock from A to B)
curl -s -X PATCH $BASE/transfers/$TID/status -H "Content-Type: application/json" \
  -d '{"status":"COMPLETED"}'

# Check stock levels and history
curl -s $BASE/warehouses/$WH1/stock
curl -s $BASE/warehouses/$WH2/stock
curl -s $BASE/transfers
```

## API reference

| Method | Path                          | Description                                     |
|--------|-------------------------------|--------------------------------------------------|
| POST   | `/api/warehouses`             | Create warehouse                                  |
| GET    | `/api/warehouses`             | List warehouses                                   |
| GET    | `/api/warehouses/{id}/stock`  | Stock levels for a warehouse                      |
| PUT    | `/api/warehouses/{id}/stock`  | Set stock quantity of a product at a warehouse    |
| POST   | `/api/products`               | Create product                                    |
| GET    | `/api/products`               | List products                                     |
| POST   | `/api/transfers`              | Create transfer request                           |
| GET    | `/api/transfers`              | List transfers (filter by `status`, `warehouse_id`) |
| GET    | `/api/transfers/{id}`         | Transfer detail                                   |
| PATCH  | `/api/transfers/{id}/status`  | Transition status to `COMPLETED` or `CANCELLED`   |

Full interactive docs at `/docs` (Swagger) or `/redoc`.

## Business rules

- A transfer starts as `PENDING`. Source and destination warehouse must differ, and the
  source must have sufficient stock at creation time.
- Transitioning a transfer to `COMPLETED` deducts the quantity from the source
  warehouse's stock and adds it to the destination's, atomically, re-validating stock
  to guard against race conditions.
- Transitioning to `CANCELLED` leaves stock untouched.
- `COMPLETED` and `CANCELLED` are terminal — no further transitions are allowed.

## Deployment (Render)

This repo includes a `render.yaml` blueprint (one Docker web service + a managed
Postgres database).

1. Push this repo to GitHub.
2. In Render, choose **New > Blueprint**, point it at the repo — it will read
   `render.yaml` and provision the web service and database together.
3. Render builds the `Dockerfile`, runs migrations on container start, and serves the
   app on the assigned URL.
4. Optionally, open a shell on the service and run
   `python manage.py createsuperuser` to get admin access.

Any other Docker-friendly host (Railway, Fly.io, etc.) works the same way: build the
`Dockerfile`, set `DATABASE_URL` to a Postgres instance, set `DJANGO_SECRET_KEY`, and
run the container.

## Environment variables

| Variable            | Description                                      | Default (local) |
|----------------------|--------------------------------------------------|------------------|
| `DJANGO_SECRET_KEY`  | Django secret key                                | insecure dev key |
| `DEBUG`              | Django debug mode (`true`/`false`)               | `true`           |
| `ALLOWED_HOSTS`      | Comma-separated allowed hosts                    | `*`              |
| `DATABASE_URL`       | Postgres connection string; unset = local SQLite | unset (SQLite)   |
