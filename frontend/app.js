const API = "/api";

function showMessage(text, type) {
  const el = document.getElementById("global-msg");
  el.textContent = text;
  el.className = `msg ${type}`;
  setTimeout(() => { el.className = "msg"; }, 4000);
}

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

// ---------- Navigation ----------
document.querySelectorAll("nav button").forEach((btn) => {
  btn.addEventListener("click", () => switchView(btn.dataset.view));
});

function switchView(view) {
  document.querySelectorAll("nav button").forEach((b) =>
    b.classList.toggle("active", b.dataset.view === view)
  );
  document.querySelectorAll(".view").forEach((v) =>
    v.classList.toggle("active", v.id === `view-${view}`)
  );
  if (view === "dashboard") loadDashboard();
  if (view === "new-transfer") loadTransferForm();
  if (view === "transfers") loadTransfers();
  if (view === "setup") loadSetup();
}

// ---------- Dashboard ----------
async function loadDashboard() {
  const el = document.getElementById("dashboard-content");
  el.textContent = "Loading...";
  try {
    const warehouses = await api("/warehouses");
    if (warehouses.length === 0) {
      el.innerHTML = '<p class="muted">No warehouses yet. Create one in the Setup tab.</p>';
      return;
    }
    let html = "";
    for (const wh of warehouses) {
      const stock = await api(`/warehouses/${wh.id}/stock`);
      html += `<h3>${wh.name} <span class="muted">${wh.location || ""}</span></h3>`;
      if (stock.length === 0) {
        html += '<p class="muted">No stock recorded.</p>';
      } else {
        html += `<table><thead><tr><th>Product</th><th>SKU</th><th>Quantity</th></tr></thead><tbody>`;
        for (const s of stock) {
          html += `<tr><td>${s.product_name}</td><td>${s.sku}</td><td>${s.quantity}</td></tr>`;
        }
        html += `</tbody></table>`;
      }
    }
    el.innerHTML = html;
  } catch (err) {
    el.innerHTML = `<p class="muted">Failed to load: ${err.message}</p>`;
  }
}

// ---------- New Transfer ----------
async function loadTransferForm() {
  const [warehouses, products] = await Promise.all([api("/warehouses"), api("/products")]);
  fillSelect("source-warehouse", warehouses);
  fillSelect("destination-warehouse", warehouses);
  fillSelect("transfer-product", products, "name");
}

function fillSelect(id, items, labelKey = "name") {
  const select = document.getElementById(id);
  select.innerHTML = items
    .map((item) => `<option value="${item.id}">${item[labelKey]}</option>`)
    .join("");
}

document.getElementById("transfer-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/transfers", {
      method: "POST",
      body: JSON.stringify({
        source_warehouse_id: Number(document.getElementById("source-warehouse").value),
        destination_warehouse_id: Number(document.getElementById("destination-warehouse").value),
        product_id: Number(document.getElementById("transfer-product").value),
        quantity: Number(document.getElementById("transfer-quantity").value),
      }),
    });
    showMessage("Transfer request created.", "success");
    e.target.reset();
    switchView("transfers");
  } catch (err) {
    showMessage(err.message, "error");
  }
});

// ---------- Transfers ----------
document.getElementById("filter-status").addEventListener("change", loadTransfers);

async function loadTransfers() {
  const el = document.getElementById("transfers-content");
  el.textContent = "Loading...";
  const status = document.getElementById("filter-status").value;
  try {
    const query = status ? `?status=${status}` : "";
    const transfers = await api(`/transfers${query}`);
    if (transfers.length === 0) {
      el.innerHTML = '<p class="muted">No transfers found.</p>';
      return;
    }
    let html = `<table><thead><tr>
      <th>ID</th><th>Product</th><th>From</th><th>To</th><th>Qty</th><th>Status</th><th>Created</th><th>Actions</th>
    </tr></thead><tbody>`;
    for (const t of transfers) {
      html += `<tr>
        <td>${t.id}</td>
        <td>${t.product_name}</td>
        <td>${t.source_warehouse_name}</td>
        <td>${t.destination_warehouse_name}</td>
        <td>${t.quantity}</td>
        <td><span class="badge ${t.status}">${t.status}</span></td>
        <td>${new Date(t.created_at).toLocaleString()}</td>
        <td class="actions">
          ${t.status === "PENDING" ? `
            <button class="complete" data-id="${t.id}" data-action="COMPLETED">Complete</button>
            <button class="cancel" data-id="${t.id}" data-action="CANCELLED">Cancel</button>
          ` : ""}
        </td>
      </tr>`;
    }
    html += "</tbody></table>";
    el.innerHTML = html;

    el.querySelectorAll("button[data-action]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          await api(`/transfers/${btn.dataset.id}/status`, {
            method: "PATCH",
            body: JSON.stringify({ status: btn.dataset.action }),
          });
          showMessage(`Transfer #${btn.dataset.id} ${btn.dataset.action.toLowerCase()}.`, "success");
          loadTransfers();
        } catch (err) {
          showMessage(err.message, "error");
        }
      });
    });
  } catch (err) {
    el.innerHTML = `<p class="muted">Failed to load: ${err.message}</p>`;
  }
}

// ---------- Setup ----------
async function loadSetup() {
  const [warehouses, products] = await Promise.all([api("/warehouses"), api("/products")]);
  fillSelect("stock-warehouse", warehouses);
  fillSelect("stock-product", products, "name");
}

document.getElementById("warehouse-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/warehouses", {
      method: "POST",
      body: JSON.stringify({
        name: document.getElementById("warehouse-name").value,
        location: document.getElementById("warehouse-location").value,
      }),
    });
    showMessage("Warehouse created.", "success");
    e.target.reset();
    loadSetup();
  } catch (err) {
    showMessage(err.message, "error");
  }
});

document.getElementById("product-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/products", {
      method: "POST",
      body: JSON.stringify({
        name: document.getElementById("product-name").value,
        sku: document.getElementById("product-sku").value,
      }),
    });
    showMessage("Product created.", "success");
    e.target.reset();
    loadSetup();
  } catch (err) {
    showMessage(err.message, "error");
  }
});

document.getElementById("stock-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const warehouseId = document.getElementById("stock-warehouse").value;
    await api(`/warehouses/${warehouseId}/stock`, {
      method: "PUT",
      body: JSON.stringify({
        product_id: Number(document.getElementById("stock-product").value),
        quantity: Number(document.getElementById("stock-quantity").value),
      }),
    });
    showMessage("Stock level updated.", "success");
  } catch (err) {
    showMessage(err.message, "error");
  }
});

// ---------- Init ----------
loadDashboard();
