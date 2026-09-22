const API_STORAGE_KEY = 'rapijob_api_base';
const TOKEN_STORAGE_KEY = 'rapijob_token';
const USER_STORAGE_KEY = 'rapijob_user';

const authMessage = document.getElementById('authMessage');
const orderMessage = document.getElementById('orderMessage');
const servicesList = document.getElementById('servicesList');
const apiBaseInput = document.getElementById('apiBaseInput');
const serviceSelect = document.getElementById('serviceSelect');

const state = {
  token: localStorage.getItem(TOKEN_STORAGE_KEY) || '',
  user: JSON.parse(localStorage.getItem(USER_STORAGE_KEY) || 'null'),
  services: [],
};

function getApiBase() {
  const stored = localStorage.getItem(API_STORAGE_KEY);
  if (stored) return stored;
  const current = apiBaseInput.value.trim();
  if (current) {
    localStorage.setItem(API_STORAGE_KEY, current);
  }
  return current || 'http://localhost:8000';
}

function setApiBase() {
  const value = apiBaseInput.value.trim() || 'http://localhost:8000';
  localStorage.setItem(API_STORAGE_KEY, value);
  showMessage(authMessage, `API configurada: ${value}`, 'info');
}

function showMessage(element, text, type = 'info') {
  element.textContent = text;
  element.className = `message ${type}`;
}

function updateAuthUI() {
  const logoutBtn = document.getElementById('logoutBtn');
  if (state.token) {
    logoutBtn.classList.remove('hidden');
  } else {
    logoutBtn.classList.add('hidden');
  }
}

async function apiFetch(path, options = {}) {
  const base = getApiBase();
  const headers = new Headers(options.headers || {});

  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (state.token) {
    headers.set('Authorization', `Bearer ${state.token}`);
  }

  const response = await fetch(`${base}${path}`, {
    ...options,
    headers,
  });

  const text = await response.text();
  let payload = text;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch (error) {
    payload = text;
  }

  if (!response.ok) {
    const detail = payload?.detail || payload?.message || 'Error de la API';
    throw new Error(detail);
  }

  return payload;
}

async function loadProfile() {
  if (!state.token) return;

  try {
    const data = await apiFetch('/api/auth/me');
    state.user = data;
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.error(error);
    logout();
  }
}

function renderServices(services) {
  servicesList.innerHTML = '';

  if (!services.length) {
    servicesList.innerHTML = '<p>No hay servicios disponibles.</p>';
    return;
  }

  services.forEach((service) => {
    const card = document.createElement('article');
    card.className = 'service-card';
    card.innerHTML = `
      <h4>${service.nombre_servicio}</h4>
      <p>${service.descripcion || 'Sin descripción disponible.'}</p>
      <div class="service-meta">
        <span>€ ${Number(service.precio_base).toFixed(2)}</span>
        <span>${service.duracion_estimada_minutos || 60} min</span>
      </div>
    `;
    servicesList.appendChild(card);
  });

  serviceSelect.innerHTML = '<option value="">Selecciona un servicio</option>' +
    services
      .map((service) => `<option value="${service.id_servicio}">${service.nombre_servicio} - € ${Number(service.precio_base).toFixed(2)}</option>`)
      .join('');
}

async function loadServices() {
  try {
    const services = await apiFetch('/api/servicios/');
    state.services = services;
    renderServices(services);
  } catch (error) {
    console.error(error);
    showMessage(authMessage, 'Necesitas iniciar sesión para ver los servicios.', 'error');
    servicesList.innerHTML = '<p>Inicia sesión para cargar los servicios.</p>';
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value.trim();

  try {
    const data = await apiFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, contraseña: password }),
    });

    state.token = data.access_token;
    localStorage.setItem(TOKEN_STORAGE_KEY, state.token);
    updateAuthUI();
    showMessage(authMessage, 'Sesión iniciada correctamente.', 'success');
    await loadProfile();
    await loadServices();
  } catch (error) {
    showMessage(authMessage, error.message, 'error');
  }
}

async function handleRegister(event) {
  event.preventDefault();

  const payload = {
    nombre: document.getElementById('regNombre').value.trim(),
    apellido: document.getElementById('regApellido').value.trim(),
    email: document.getElementById('regEmail').value.trim(),
    telefono: document.getElementById('regTelefono').value.trim(),
    tipo_usuario: document.getElementById('regTipoUsuario').value,
    documento_identidad: document.getElementById('regDocumento').value.trim(),
    contraseña: document.getElementById('regPassword').value.trim(),
  };

  try {
    await apiFetch('/api/auth/registro', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showMessage(authMessage, 'Usuario registrado correctamente. Ahora puedes iniciar sesión.', 'success');
    document.getElementById('registerForm').reset();
  } catch (error) {
    showMessage(authMessage, error.message, 'error');
  }
}

async function handleCreateOrder(event) {
  event.preventDefault();

  if (!state.token) {
    showMessage(orderMessage, 'Debes iniciar sesión para crear una orden.', 'error');
    return;
  }

  const payload = {
    id_servicio: Number(document.getElementById('serviceSelect').value),
    id_slot_cita: Number(document.getElementById('slotId').value),
    id_metodo_pago: Number(document.getElementById('metodoPagoId').value),
    ubicacion_servicio: document.getElementById('ubicacion').value.trim(),
    descripcion_problema: document.getElementById('descripcion').value.trim(),
    notas_adicionales: document.getElementById('notas').value.trim(),
    precio_negociado: document.getElementById('precioNegociado').value ? Number(document.getElementById('precioNegociado').value) : null,
  };

  try {
    const data = await apiFetch('/api/ordenes/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showMessage(orderMessage, `Orden creada correctamente. ID: ${data.id_orden}`, 'success');
    document.getElementById('orderForm').reset();
  } catch (error) {
    showMessage(orderMessage, error.message, 'error');
  }
}

function logout() {
  state.token = '';
  state.user = null;
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
  updateAuthUI();
  showMessage(authMessage, 'Has cerrado sesión.', 'info');
  servicesList.innerHTML = '<p>Inicia sesión para ver los servicios.</p>';
}

function init() {
  apiBaseInput.value = getApiBase();
  updateAuthUI();

  if (state.token) {
    loadProfile();
  }

  loadServices();

  document.getElementById('loginForm').addEventListener('submit', handleLogin);
  document.getElementById('registerForm').addEventListener('submit', handleRegister);
  document.getElementById('orderForm').addEventListener('submit', handleCreateOrder);
  document.getElementById('saveApiBtn').addEventListener('click', setApiBase);
  document.getElementById('logoutBtn').addEventListener('click', logout);
  document.getElementById('refreshServicesBtn').addEventListener('click', loadServices);
}

init();
