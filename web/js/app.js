const BASE_URL = "/api";
const PLACEHOLDER_IMG =
  "https://covers.openlibrary.org/b/id/10523364-L.jpg";

async function safeJson(res) {
  const text = await res.text();
  try { return JSON.parse(text); }
  catch { return { raw: text }; }
}

function logout() {
  localStorage.removeItem("token");
  window.location.replace("login.html");
}

/* LOGIN */
async function login() {
  try {
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");

    const email = emailInput.value;
    const password = passwordInput.value;

    if (!email || !password) {
      document.getElementById("error").innerText =
        "Email e password são obrigatórios";
      return;
    }

    const res = await fetch(`${BASE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await safeJson(res);

    if (!res.ok) {
      document.getElementById("error").innerText =
        "Credenciais inválidas";
      return;
    }

    localStorage.setItem("token", data.access_token);
    window.location.replace("catalog.html");

  } catch (err) {
    document.getElementById("error").innerText =
      "Erro no login: " + err.toString();
  }
}


/* AUTH FETCH */
async function authFetch(url, options = {}) {
  const token = localStorage.getItem("token");
  if (!token) window.location.replace("login.html");

  options.headers = options.headers || {};
  options.headers.Authorization = `Bearer ${token}`;
  if (options.body) options.headers["Content-Type"] = "application/json";

  const res = await fetch(url, options);
  const data = await safeJson(res);
  if (!res.ok) throw data;
  return data;
}

/* CATALOG */
async function loadBooks() {
  const books = await authFetch(`${BASE_URL}/catalog/books/`);
  const el = document.getElementById("books");
  el.innerHTML = "";

  books.forEach(b => {
    el.innerHTML += `
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <img src="${PLACEHOLDER_IMG}" class="card-img-top">
          <div class="card-body">
            <h5>${b.title}</h5>
            <button class="btn btn-primary w-100"
              onclick="createExemplar(${b.id})">
              Criar Exemplar
            </button>
          </div>
        </div>
      </div>`;
  });
}

async function createBook() {
  const title = bookTitle.value;
  await authFetch(`${BASE_URL}/catalog/books/`, {
    method: "POST",
    body: JSON.stringify({ title })
  });
  loadBooks();
}

async function createExemplar(id) {
  await authFetch(`${BASE_URL}/catalog/exemplars/`, {
    method: "POST",
    body: JSON.stringify({ book_id: id })
  });
  alert("Exemplar criado");
}

/* RESERVATIONS */
async function loadReservations() {
  const res = await authFetch(`${BASE_URL}/reservations/`);
  const tbody = document.getElementById("reservations");
  tbody.innerHTML = "";

  res.forEach(r => {
    tbody.innerHTML += `
      <tr>
        <td>${r.id}</td>
        <td>${r.items.length}</td>
        <td>
          <button class="btn btn-primary btn-sm"
            onclick="location.href='payments.html?reservation=${r.id}'">
            Pagar
          </button>
        </td>
      </tr>`;
  });
}

/* PAYMENTS */
async function createPayment() {
  const params = new URLSearchParams(window.location.search);
  const reservation = params.get("reservation");

  await authFetch(`${BASE_URL}/payments/`, {
    method: "POST",
    body: JSON.stringify({
      reservation_id: Number(reservation),
      amount: Number(amount.value),
      method: method.value
    })
  });

  alert("Pagamento efetuado");
  window.location.replace("reservations.html");
}
