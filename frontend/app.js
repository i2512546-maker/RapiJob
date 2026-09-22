const API_STORAGE_KEY = 'rapijob_api_base';
const TOKEN_STORAGE_KEY = 'rapijob_token';
const USER_STORAGE_KEY = 'rapijob_user';

const state = {
  token: localStorage.getItem(TOKEN_STORAGE_KEY) || '',
  user: JSON.parse(localStorage.getItem(USER_STORAGE_KEY) || 'null'),
  services: [],
};

const $ = (selector) => document.querySelector(selector);
const apiBaseInput = $('#apiBaseInput');
const servicesList = $('#servicesList');

function getApiBase() {
  return (localStorage.getItem(API_STORAGE_KEY) || apiBaseInput.value || window.location.origin || 'http://localhost:8000').trim().replace(/\/$/, '');
}

function renderServiceOptions() {
  $('#serviceSelect').innerHTML = '<option value="">Selecciona un servicio</option>' +
    state.services.map((service) => `<option value="${service.id_servicio}">${escapeHtml(service.nombre_servicio)} · $${Number(service.precio_base || 0).toFixed(2)}</option>`).join('');
}

async function loadBookingOptions() {
  if (!state.token || state.user?.tipo_usuario !== 'cliente') return;
  try {
    const [slots, payments] = await Promise.all([
      apiFetch('/api/admin/slots-citas/'),
      apiFetch('/api/admin/metodos-pago/'),
    ]);
    $('#slotSelect').innerHTML = '<option value="">Selecciona un horario</option>' +
      slots.map((slot) => `<option value="${slot.id_slot}">${new Date(slot.hora_inicio).toLocaleString('es-CO')} - ${new Date(slot.hora_fin).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}</option>`).join('');
    $('#paymentSelect').innerHTML = '<option value="">Selecciona un método</option>' +
      payments.map((payment) => `<option value="${payment.id_metodo}">${escapeHtml(payment.nombre_metodo)}</option>`).join('');
  } catch (error) { showToast(error.message); }
}

async function handleCreateOrder(event) {
  event.preventDefault();
  try {
    const data = await apiFetch('/api/ordenes/', { method: 'POST', body: JSON.stringify({
      id_servicio: Number($('#serviceSelect').value),
      id_slot_cita: Number($('#slotSelect').value),
      id_metodo_pago: Number($('#paymentSelect').value),
      ubicacion_servicio: $('#ubicacion').value.trim(),
      descripcion_problema: $('#descripcion').value.trim(),
      notas_adicionales: $('#notas').value.trim() || null,
    }) });
    $('#orderForm').reset();
    $('#orderMessage').textContent = `Solicitud creada correctamente. Orden #${data.id_orden}`;
    $('#orderMessage').className = 'message success';
    showToast('Solicitud enviada a los técnicos');
  } catch (error) {
    $('#orderMessage').textContent = error.message;
    $('#orderMessage').className = 'message error';
  }
}

async function loadOrders() {
  if (!state.token || state.user?.tipo_usuario !== 'tecnico') return;
  try {
    const orders = await apiFetch('/api/ordenes/');
    $('#ordersList').innerHTML = orders.length ? orders.map((order) => `<article class="order-card"><span class="order-status">${escapeHtml(order.estado_orden)}</span><h3>Solicitud #${order.id_orden}</h3><p>${escapeHtml(order.descripcion_problema)}</p><p><strong>Ubicación:</strong> ${escapeHtml(order.ubicacion_servicio)}<br><strong>Presupuesto:</strong> $${Number(order.precio_final || order.precio_base).toFixed(2)}</p>${order.estado_orden === 'pendiente' ? `<button class="button button-primary accept-order" data-id="${order.id_orden}">Aceptar solicitud</button>` : ''}</article>`).join('') : '<div class="empty-state">No hay solicitudes disponibles.</div>';
    document.querySelectorAll('.accept-order').forEach((button) => button.addEventListener('click', async () => {
      try { await apiFetch(`/api/ordenes/${button.dataset.id}/aceptar`, { method: 'PATCH' }); showToast('Solicitud aceptada'); loadOrders(); } catch (error) { showToast(error.message); }
    }));
  } catch (error) { showToast(error.message); }
}

function showMessage(text, type = 'info') {
  const element = $('#authMessage');
  element.textContent = text;
  element.className = `message ${type}`;
}

function showToast(text) {
  const toast = $('#toast');
  toast.textContent = text;
  toast.classList.add('visible');
  window.setTimeout(() => toast.classList.remove('visible'), 3200);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[character]));
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (state.token) headers.set('Authorization', `Bearer ${state.token}`);
  const response = await fetch(`${getApiBase()}${path}`, { ...options, headers });
  const text = await response.text();
  let payload = text;
  try { payload = text ? JSON.parse(text) : null; } catch { /* La API puede responder texto plano. */ }
  if (!response.ok) throw new Error(payload?.detail || payload?.message || 'No se pudo completar la solicitud.');
  return payload;
}

function updateAuthUI() {
  const loggedIn = Boolean(state.token);
  $('#logoutBtn').classList.toggle('hidden', !loggedIn);
  $('#userGreeting').classList.toggle('hidden', !loggedIn);
  $('#userGreeting').textContent = loggedIn ? `Hola, ${state.user?.nombre || 'bienvenido'}` : '';
  $('.nav-cta').textContent = loggedIn ? 'Solicitar servicio ↗' : 'Comenzar ↗';
  $('#contratar').classList.toggle('hidden', !loggedIn || state.user?.tipo_usuario !== 'cliente');
  $('#technicianPanel').classList.toggle('hidden', !loggedIn || state.user?.tipo_usuario !== 'tecnico');
  if (loggedIn && state.user?.tipo_usuario === 'cliente') loadBookingOptions();
  if (loggedIn && state.user?.tipo_usuario === 'tecnico') loadOrders();
}

function renderServices(services) {
  servicesList.innerHTML = '';
  if (!services.length) {
    servicesList.innerHTML = '<div class="empty-state">No hay servicios disponibles por ahora.</div>';
    return;
  }
  const icons = ['⌂', '✦', '⚙', '◒', '✚', '◇'];
  services.forEach((service, index) => {
    const card = document.createElement('article');
    card.className = 'service-card';
    card.innerHTML = `<div class="service-icon">${icons[index % icons.length]}</div>
      <h3>${escapeHtml(service.nombre_servicio || 'Servicio')}</h3>
      <p>${escapeHtml(service.descripcion || 'Soluciones profesionales adaptadas a tus necesidades.')}</p>
      <div class="service-meta"><strong>Desde $${Number(service.precio_base || 0).toFixed(2)}</strong><span>${service.duracion_estimada_minutos || 60} min aprox.</span></div>`;
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
    servicesList.innerHTML = '<div class="empty-state">Inicia sesión para consultar los servicios.</div>';
    if (state.token) showToast(error.message);
  }
}

async function loadProfile() {
  if (!state.token) return;
  try {
    state.user = await apiFetch('/api/auth/me');
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(state.user));
    updateAuthUI();
  } catch {
    logout(false);
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  try {
    const data = await apiFetch('/api/auth/login', { method: 'POST', body: JSON.stringify({ email: $('#loginEmail').value.trim(), contraseña: $('#loginPassword').value }) });
    state.token = data.access_token;
    localStorage.setItem(TOKEN_STORAGE_KEY, state.token);
    await loadProfile();
    updateAuthUI();
    showMessage('Sesión iniciada correctamente. ¡Qué bueno verte!', 'success');
    showToast('Bienvenido a RapiJob');
    await loadServices();
  } catch (error) { showMessage(error.message, 'error'); } finally { button.disabled = false; }
}

async function handleRegister(event) {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  const payload = { nombre: $('#regNombre').value.trim(), apellido: $('#regApellido').value.trim(), email: $('#regEmail').value.trim(), telefono: $('#regTelefono').value.trim(), tipo_usuario: $('#regTipoUsuario').value, documento_identidad: $('#regDocumento').value, contraseña: $('#regPassword').value };
  try {
    await apiFetch('/api/auth/registro', { method: 'POST', body: JSON.stringify(payload) });
    $('#registerForm').reset();
    $('#loginEmail').value = payload.email;
    document.querySelector('[data-tab="login"]').click();
    showMessage('Cuenta creada. Ahora puedes iniciar sesión.', 'success');
  } catch (error) { showMessage(error.message, 'error'); } finally { button.disabled = false; }
}

function logout(show = true) {
  state.token = ''; state.user = null;
  localStorage.removeItem(TOKEN_STORAGE_KEY); localStorage.removeItem(USER_STORAGE_KEY);
  updateAuthUI();
  if (show) { showMessage('Has cerrado sesión correctamente.', 'info'); showToast('Sesión cerrada'); }
}

function initTabs() {
  document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((item) => item.classList.toggle('active', item === tab));
    $('#loginForm').classList.toggle('hidden', tab.dataset.tab !== 'login');
    $('#registerForm').classList.toggle('hidden', tab.dataset.tab !== 'register');
  }));
}

function init() {
  apiBaseInput.value = getApiBase();
  updateAuthUI(); initTabs(); loadServices(); loadProfile();
  $('#loginForm').addEventListener('submit', handleLogin);
  $('#registerForm').addEventListener('submit', handleRegister);
  $('#orderForm').addEventListener('submit', handleCreateOrder);
  $('#logoutBtn').addEventListener('click', () => logout());
  $('#refreshServicesBtn').addEventListener('click', loadServices);
  $('#saveApiBtn').addEventListener('click', () => { localStorage.setItem(API_STORAGE_KEY, apiBaseInput.value.trim().replace(/\/$/, '')); showToast('URL de API guardada'); loadServices(); });
  $('#refreshOrdersBtn').addEventListener('click', loadOrders);
}

init();
