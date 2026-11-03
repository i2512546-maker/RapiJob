const API_STORAGE_KEY = 'rapijob_api_base';
const TOKEN_STORAGE_KEY = 'rapijob_token';
const USER_STORAGE_KEY = 'rapijob_user';

const state = {
  token: localStorage.getItem(TOKEN_STORAGE_KEY) || '',
  user: null,
  services: [],
};

const $ = (selector) => document.querySelector(selector);
const apiBaseInput = $('#apiBaseInput');
const servicesList = $('#servicesList');

function getApiBase() {
  // Por defecto, frontend y API se sirven desde el mismo dominio.
  return (localStorage.getItem(API_STORAGE_KEY) || window.location.origin || 'http://localhost:8000')
    .trim().replace(/\/$/, '');
}

function money(value) {
  return new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(Number(value || 0));
}

function showMessage(message, type = 'info') {
  const element = $('#authMessage');
  element.textContent = message;
  element.className = \`message \${type}\`;
}

function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('visible');
  window.setTimeout(() => toast.classList.remove('visible'), 3200);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;',
  }[character]));
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (state.token) headers.set('Authorization', \`Bearer \${state.token}\`);
  let response;
  try {
    response = await fetch(\`\${getApiBase()}\${path}\`, { ...options, headers });
  } catch {
    throw new Error('No se pudo conectar con RapiJob. Comprueba tu conexión o la dirección de la API.');
  }
  const raw = await response.text();
  let payload = raw;
  try { payload = raw ? JSON.parse(raw) : null; } catch { /* respuesta no JSON */ }
  if (!response.ok) {
    const detail = payload?.detail;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || payload?.message || 'No se pudo completar la solicitud.');
  }
  return payload;
}

function renderServiceOptions() {
  const select = $('#serviceSelect');
  if (!select) return;
  select.innerHTML = '<option value="">Selecciona un servicio</option>' +
    state.services.map((service) =>
      \`<option value="\${service.id_servicio}">\${escapeHtml(service.nombre_servicio)} · \${money(service.precio_base)}</option>\`
    ).join('');
}

function renderServices(services) {
  servicesList.innerHTML = '';
  if (!services.length) {
    servicesList.innerHTML = '<div class="empty-state">Todavía no hay servicios publicados.</div>';
    return;
  }
  const icons = ['⌂', '✦', '⚙', '◒', '✚', '◇'];
  services.forEach((service, index) => {
    const card = document.createElement('article');
    card.className = 'service-card';
    card.innerHTML = \`<div class="service-icon">\${icons[index % icons.length]}</div>
      <h3>\${escapeHtml(service.nombre_servicio)}</h3>
      <p>\${escapeHtml(service.descripcion || 'Servicio técnico profesional.')}</p>
      <div class="service-meta"><strong>Desde \${money(service.precio_base)}</strong><span>\${service.duracion_estimada_minutos || 60} min aprox.</span></div>
      <small class="price-note">Precio referencial; se confirma según el diagnóstico.</small>\`;
    servicesList.appendChild(card);
  });
}

async function loadServices() {
  servicesList.innerHTML = '<div class="loading-state"><span class="spinner"></span>Cargando servicios...</div>';
  try {
    state.services = await apiFetch('/api/servicios/');
    renderServices(state.services);
    renderServiceOptions();
  } catch (error) {
    servicesList.innerHTML = \`<div class="empty-state">\${escapeHtml(error.message)}</div>\`;
  }
}

async function loadBookingOptions() {
  if (!state.token || state.user?.tipo_usuario !== 'cliente') return;
  try {
    const slots = await apiFetch('/api/admin/slots-citas/');
    $('#slotSelect').innerHTML = '<option value="">Selecciona un horario</option>' +
      slots.map((slot) => {
        const start = new Date(slot.hora_inicio);
        const end = new Date(slot.hora_fin);
        return \`<option value="\${slot.id_slot}">\${start.toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' })} - \${end.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })}</option>\`;
      }).join('');
    if (!slots.length) $('#slotSelect').innerHTML = '<option value="">No hay horarios disponibles</option>';
  } catch (error) {
    showToast(error.message);
  }
}

async function loadOrders() {
  if (!state.token || !state.user) return;
  try {
    const orders = await apiFetch('/api/ordenes/');
    const target = state.user.tipo_usuario === 'tecnico' ? $('#ordersList') : $('#clientOrdersList');
    if (!target) return;
    target.innerHTML = orders.length ? orders.map((order) => \`
      <article class="order-card">
        <span class="order-status">\${escapeHtml(order.estado_orden)}</span>
        <h3>Solicitud #\${order.id_orden}</h3>
        <p>\${escapeHtml(order.descripcion_problema)}</p>
        <p><strong>Fecha:</strong> \${new Date(order.fecha_programada).toLocaleString('es-PE')}</p>
        <p><strong>Ubicación:</strong> \${escapeHtml(order.ubicacion_servicio)}</p>
        <p><strong>Precio referencial:</strong> \${money(order.precio_final)}</p>
        \${state.user.tipo_usuario === 'tecnico' && order.estado_orden === 'pendiente' ? \`<button class="button button-primary accept-order" data-id="\${order.id_orden}">Aceptar solicitud</button>\` : ''}
        \${order.estado_orden === 'pendiente' || order.estado_orden === 'aceptada' ? \`<button class="button button-outline cancel-order" data-id="\${order.id_orden}">Cancelar</button>\` : ''}
      </article>\`).join('') : '<div class="empty-state">Todavía no tienes solicitudes.</div>';

    target.querySelectorAll('.accept-order').forEach((button) => button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        await apiFetch(\`/api/ordenes/\${button.dataset.id}/aceptar\`, { method: 'PATCH' });
        showToast('Solicitud aceptada correctamente.');
        await loadOrders();
      } catch (error) { showToast(error.message); button.disabled = false; }
    }));
    target.querySelectorAll('.cancel-order').forEach((button) => button.addEventListener('click', async () => {
      if (!window.confirm('¿Deseas cancelar esta solicitud?')) return;
      button.disabled = true;
      try {
        await apiFetch(\`/api/ordenes/\${button.dataset.id}/cancelar\`, { method: 'PATCH' });
        showToast('Solicitud cancelada.');
        await loadOrders();
      } catch (error) { showToast(error.message); button.disabled = false; }
    }));
  } catch (error) {
    showToast(error.message);
  }
}

async function handleCreateOrder(event) {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    const data = await apiFetch('/api/ordenes/', {
      method: 'POST',
      body: JSON.stringify({
        id_servicio: Number($('#serviceSelect').value),
        id_slot_cita: Number($('#slotSelect').value),
        ubicacion_servicio: $('#ubicacion').value.trim(),
        descripcion_problema: $('#descripcion').value.trim(),
        notas_adicionales: $('#notas').value.trim() || null,
      }),
    });
    $('#orderForm').reset();
    $('#orderMessage').textContent = \`Solicitud #\${data.id_orden} registrada. Precio referencial: \${money(data.precio_final)}. No se realizó ningún cobro.\`;
    $('#orderMessage').className = 'message success';
    await loadBookingOptions();
    await loadOrders();
    showToast('Tu solicitud fue registrada.');
  } catch (error) {
    $('#orderMessage').textContent = error.message;
    $('#orderMessage').className = 'message error';
  } finally {
    button.disabled = false;
  }
}

function updateAuthUI() {
  const loggedIn = Boolean(state.token && state.user);
  $('#logoutBtn').classList.toggle('hidden', !loggedIn);
  $('#userGreeting').classList.toggle('hidden', !loggedIn);
  $('#userGreeting').textContent = loggedIn ? \`Hola, \${state.user.nombre}\` : '';
  $('.nav-cta').textContent = loggedIn ? 'Solicitar servicio ↗' : 'Comenzar ↗';
  $('#contratar').classList.toggle('hidden', !loggedIn || state.user.tipo_usuario !== 'cliente');
  $('#technicianPanel').classList.toggle('hidden', !loggedIn || state.user.tipo_usuario !== 'tecnico');
  $('#clientOrders').classList.toggle('hidden', !loggedIn || state.user.tipo_usuario !== 'cliente');
  if (loggedIn && state.user.tipo_usuario === 'cliente') loadBookingOptions();
  if (loggedIn) loadOrders();
}

async function loadProfile() {
  if (!state.token) {
    state.user = null;
    updateAuthUI();
    return;
  }
  try {
    state.user = await apiFetch('/api/auth/me');
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(state.user));
  } catch {
    state.token = '';
    state.user = null;
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  }
  updateAuthUI();
}

async function handleLogin(event) {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    const data = await apiFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: $('#loginEmail').value.trim(), contraseña: $('#loginPassword').value }),
    });
    state.token = data.access_token;
    localStorage.setItem(TOKEN_STORAGE_KEY, state.token);
    await loadProfile();
    if (!state.user) throw new Error('No se pudo cargar tu perfil. Intenta nuevamente.');
    updateAuthUI();
    showMessage('Sesión iniciada correctamente.', 'success');
    showToast('Bienvenido a RapiJob.');
    await loadServices();
  } catch (error) {
    showMessage(error.message, 'error');
  } finally {
    button.disabled = false;
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  const payload = {
    nombre: $('#regNombre').value.trim(),
    apellido: $('#regApellido').value.trim(),
    email: $('#regEmail').value.trim(),
    telefono: $('#regTelefono').value.trim() || null,
    tipo_usuario: $('#regTipoUsuario').value,
    documento_identidad: $('#regDocumento').value.trim() || null,
    contraseña: $('#regPassword').value,
  };
  try {
    await apiFetch('/api/auth/registro', { method: 'POST', body: JSON.stringify(payload) });
    const loginData = await apiFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: payload.email, contraseña: payload.contraseña }),
    });
    state.token = loginData.access_token;
    localStorage.setItem(TOKEN_STORAGE_KEY, state.token);
    $('#registerForm').reset();
    await loadProfile();
    updateAuthUI();
    showMessage('Tu cuenta fue creada correctamente. Ya iniciaste sesión.', 'success');
    showToast('¡Bienvenido a RapiJob!');
    await loadServices();
  } catch (error) {
    showMessage(error.message, 'error');
  } finally {
    button.disabled = false;
  }
}

function logout(show = true) {
  state.token = '';
  state.user = null;
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
  updateAuthUI();
  if (show) {
    showMessage('Has cerrado sesión correctamente.', 'info');
    showToast('Sesión cerrada.');
  }
}

function initTabs() {
  document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((item) => item.classList.toggle('active', item === tab));
    $('#loginForm').classList.toggle('hidden', tab.dataset.tab !== 'login');
    $('#registerForm').classList.toggle('hidden', tab.dataset.tab !== 'register');
  }));
}

function init() {
  if (!apiBaseInput) return;
  apiBaseInput.value = getApiBase();
  initTabs();
  $('#loginForm').addEventListener('submit', handleLogin);
  $('#registerForm').addEventListener('submit', handleRegister);
  $('#orderForm').addEventListener('submit', handleCreateOrder);
  $('#logoutBtn').addEventListener('click', () => logout());
  $('#refreshServicesBtn').addEventListener('click', loadServices);
  $('#saveApiBtn').addEventListener('click', () => {
    const value = apiBaseInput.value.trim().replace(/\/$/, '');
    if (!value || !/^https?:\/\//i.test(value)) {
      showToast('Escribe una URL válida que comience con http:// o https://.');
      return;
    }
    localStorage.setItem(API_STORAGE_KEY, value);
    showToast('Dirección de API guardada.');
    loadServices();
  });
  $('#refreshOrdersBtn').addEventListener('click', loadOrders);
  loadServices();
  loadProfile();
}

init();
