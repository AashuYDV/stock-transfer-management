def test_full_transfer_flow(client):
    wh1 = client.post("/api/warehouses", json={"name": "API-WH1", "location": "X"}).json()
    wh2 = client.post("/api/warehouses", json={"name": "API-WH2", "location": "Y"}).json()
    product = client.post("/api/products", json={"name": "Gadget", "sku": "G-1"}).json()

    client.put(
        f"/api/warehouses/{wh1['id']}/stock",
        json={"product_id": product["id"], "quantity": 30},
    )

    create_resp = client.post(
        "/api/transfers",
        json={
            "source_warehouse_id": wh1["id"],
            "destination_warehouse_id": wh2["id"],
            "product_id": product["id"],
            "quantity": 10,
        },
    )
    assert create_resp.status_code == 201
    transfer = create_resp.json()
    assert transfer["status"] == "PENDING"

    complete_resp = client.patch(
        f"/api/transfers/{transfer['id']}/status", json={"status": "COMPLETED"}
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"

    stock_source = client.get(f"/api/warehouses/{wh1['id']}/stock").json()
    stock_dest = client.get(f"/api/warehouses/{wh2['id']}/stock").json()
    assert stock_source[0]["quantity"] == 20
    assert stock_dest[0]["quantity"] == 10

    history = client.get("/api/transfers").json()
    assert len(history) == 1


def test_transfer_insufficient_stock_returns_400(client):
    wh1 = client.post("/api/warehouses", json={"name": "API-WH3", "location": "X"}).json()
    wh2 = client.post("/api/warehouses", json={"name": "API-WH4", "location": "Y"}).json()
    product = client.post("/api/products", json={"name": "Sprocket", "sku": "S-1"}).json()

    resp = client.post(
        "/api/transfers",
        json={
            "source_warehouse_id": wh1["id"],
            "destination_warehouse_id": wh2["id"],
            "product_id": product["id"],
            "quantity": 5,
        },
    )
    assert resp.status_code == 400


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
