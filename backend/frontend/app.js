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
  // En producción, el frontend y la API se sirven desde el mismo dominio.
  // Ignora una URL localhost guardada durante el desarrollo local.
  const saved = (localStorage.getItem(API_STORAGE_KEY) || '').trim().replace(/\/$/, '');
  const isLocalHost = /^(https?:\/\/)?(localhost|127\.0\.0\.1)(:\d+)?$/i.test(saved);
  const isProduction = !['localhost', '127.0.0.1'].includes(window.location.hostname);
  if (saved && !(isProduction && isLocalHost)) return saved;
  return window.location.origin || 'http://localhost:8000';
}
function parseServerDate(value) {
  if (!value) return null;
  // FastAPI serializa fechas sin zona cuando SQLAlchemy almacena UTC naive.
  return new Date(/(Z|[+-]\d{2}:\d{2})$/.test(value) ? value : value + 'Z');
}

function money(value) {
  return new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' }).format(Number(value || 0));
}

function showMessage(message, type = 'info') {
  const element = $('#authMessage');
  element.textContent = message;
  element.className = \`message \${type}\`;
}

function showToast(message, type = 'success') {
  const toast = $('#toast');
  let cleanMessage = message;

  // Nunca mostrar objetos de configuración/traducción como texto crudo.
  if (cleanMessage && typeof cleanMessage === 'object') {
    cleanMessage = cleanMessage.message || cleanMessage.detail || cleanMessage.text || '';
  }
  if (typeof cleanMessage === 'string' && cleanMessage.trim().startsWith('{')) {
    try {
      const parsed = JSON.parse(cleanMessage);
      cleanMessage = parsed.message || parsed.detail || parsed.text || '';
    } catch {
      // Conserva el texto si no es JSON válido.
    }
  }
  if (typeof cleanMessage !== 'string' || !cleanMessage.trim()) {
    cleanMessage = 'La operación se realizó correctamente.';
  }

  toast.textContent = cleanMessage;
  toast.classList.remove('toast-success', 'toast-error', 'toast-info');
  toast.classList.add(`toast-${type}`, 'visible');
  window.clearTimeout(toast.hideTimer);
  toast.hideTimer = window.setTimeout(() => {
    toast.classList.remove('visible');
  }, 3600);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;',
  }[character]));
}

function friendlyApiError(payload, raw, status) {
  const detail = payload && typeof payload === 'object' ? payload.detail : null;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => typeof item === 'string' ? item : (item && typeof item.msg === 'string' ? item.msg : '')).filter(Boolean);
    if (messages.length) return messages.join('. ');
  }
  if (detail && typeof detail === 'object') {
    const message = detail.message || detail.msg || detail.error;
    if (typeof message === 'string' && message.trim()) return message;
  }
  const message = payload && typeof payload === 'object' ? (payload.message || payload.error) : null;
  if (typeof message === 'string' && message.trim()) return message;
  if (status === 401) return 'Correo o contraseña incorrectos.';
  if (status === 403) return 'No tienes permiso para realizar esta acción.';
  if (status === 404) return 'No encontramos el recurso solicitado.';
  if (status >= 500) return 'El servicio no está disponible en este momento. Inténtalo más tarde.';
  return 'No se pudo completar la solicitud. Revisa los datos e inténtalo nuevamente.';
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set('Accept', 'application/json');
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (state.token) headers.set('Authorization', `Bearer ${state.token}`);
  let response;
  try {
    response = await fetch(`${getApiBase()}${path}`, { ...options, headers });
  } catch {
    throw new Error('No se pudo conectar con RapiJob. Comprueba tu conexión o la dirección de la API.');
  }
  const raw = await response.text();
  let payload = null;
  try { payload = raw ? JSON.parse(raw) : null; } catch { payload = null; }
  if (!response.ok) throw new Error(friendlyApiError(payload, raw, response.status));
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
    const selectedTechnician = $('#selectedTechnicianId')?.value;
    const slots = await apiFetch('/api/admin/slots-citas/' + (selectedTechnician ? '?id_tecnico=' + encodeURIComponent(selectedTechnician) : ''));
    $('#slotSelect').innerHTML = '<option value="">Selecciona un horario</option>' +
      slots.map((slot) => {
        const start = parseServerDate(slot.hora_inicio);
        const end = parseServerDate(slot.hora_fin);
        return \`<option value="\${slot.id_slot}">\${start.toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' })} - \${end.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })}</option>\`;
      }).join('');
    if (!slots.length) $('#slotSelect').innerHTML = '<option value="">No hay horarios disponibles</option>';
  } catch (error) {
    showToast(error.message);
  }
}

window.addEventListener('rapijob:technician-selected', () => loadBookingOptions());

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
        <p><strong>Fecha:</strong> \${parseServerDate(order.fecha_programada).toLocaleString('es-PE')}</p>
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
    target.querySelectorAll('.start-order, .complete-order').forEach((button) => button.addEventListener('click', async () => {
      button.disabled = true;
      const action = button.classList.contains('start-order') ? 'iniciar' : 'completar';
      try { await apiFetch(`/api/ordenes/${button.dataset.id}/${action}`, { method: 'PATCH' }); showToast(action === 'iniciar' ? 'Trabajo iniciado.' : 'Trabajo completado.'); await loadOrders(); }
      catch (error) { showToast(error.message); button.disabled = false; }
    }));
    target.querySelectorAll('.review-order').forEach((form) => form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(form).entries());
      values.calificacion_servicio = Number(values.calificacion_servicio);
      values.calificacion_tecnico = Number(values.calificacion_tecnico);
      try { await apiFetch(`/api/ordenes/${form.dataset.id}/resena`, { method: 'POST', body: JSON.stringify(values) }); showToast('Gracias por tu calificación.'); await loadOrders(); }
      catch (error) { showToast(error.message); }
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
        id_tecnico: $('#selectedTechnicianId')?.value ? Number($('#selectedTechnicianId').value) : null,
        latitud: $('#selectedLatitude')?.value ? Number($('#selectedLatitude').value) : null,
        longitud: $('#selectedLongitude')?.value ? Number($('#selectedLongitude').value) : null,
        id_slot_cita: Number($('#slotSelect').value),
        ubicacion_servicio: $('#ubicacion').value.trim(),
        descripcion_problema: $('#descripcion').value.trim(),
        notas_adicionales: $('#notas').value.trim() || null,
      }),
    });
    const photoFiles = Array.from($('#orderPhotos')?.files || []);
    for (const photo of photoFiles) {
      const upload = new FormData();
      upload.append('archivo', photo);
      await apiFetch(`/api/ordenes/${data.id_orden}/adjuntos`, { method: 'POST', body: upload });
    }
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

async function handleCreateSlot(event) {
  event.preventDefault();
  const button = event.submitter;
  const startValue = $('#slotStart').value;
  const endValue = $('#slotEnd').value;
  const start = new Date(startValue);
  const end = new Date(endValue);
  if (!startValue || !endValue || Number.isNaN(start.getTime()) || end <= start) {
    $('#slotMessage').textContent = 'Selecciona un rango de fechas y horas válido.';
    $('#slotMessage').className = 'message error';
    return;
  }
  button.disabled = true;
  try {
    await apiFetch('/api/admin/slots-citas/', {
      method: 'POST',
      body: JSON.stringify({
        fecha: start.toISOString(),
        hora_inicio: start.toISOString(),
        hora_fin: end.toISOString(),
        capacidad_maxima: Number($('#slotCapacity').value || 1),
      }),
    });
    $('#slotForm').reset();
    $('#slotCapacity').value = '1';
    $('#slotMessage').textContent = 'Horario publicado. Ya está disponible para los clientes.';
    $('#slotMessage').className = 'message success';
    showToast('Horario publicado correctamente.');
  } catch (error) {
    $('#slotMessage').textContent = error.message;
    $('#slotMessage').className = 'message error';
  } finally {
    button.disabled = false;
  }
}

function updateAuthUI() {
  const loggedIn = Boolean(state.token && state.user);
  const logoutButton = $('#logoutBtn');
  const greeting = $('#userGreeting');
  const navLogin = $('.nav-login');
  const bookingSection = $('#contratar');
  const technicianPanel = $('#technicianPanel');
  const clientOrders = $('#clientOrders');

  if (logoutButton) logoutButton.classList.toggle('hidden', !loggedIn);
  if (greeting) {
    greeting.classList.toggle('hidden', !loggedIn);
    greeting.textContent = loggedIn ? `Hola, ${state.user.nombre}` : '';
  }

  // El HTML actual utiliza .nav-login; .nav-cta no existe.
  if (navLogin) {
    navLogin.href = loggedIn ? '#contratar' : '#acceso';
    navLogin.innerHTML = loggedIn
      ? 'Solicitar servicio <span>→</span>'
      : 'Iniciar sesión <span>→</span>';
  }

  if (bookingSection) {
    bookingSection.classList.toggle('hidden', !loggedIn || state.user.tipo_usuario !== 'cliente');
  }
  if (technicianPanel) {
    technicianPanel.classList.toggle('hidden', !loggedIn || state.user.tipo_usuario !== 'tecnico');
  }
  if (clientOrders) {
    clientOrders.classList.toggle('hidden', !loggedIn || state.user.tipo_usuario !== 'cliente');
  }

  if (loggedIn && state.user.tipo_usuario === 'cliente') loadBookingOptions();
  if (loggedIn) loadOrders();
  window.dispatchEvent(new Event('rapijob:session-updated'));
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
  const button = event.submitter || $('#loginForm button[type="submit"]');
  if (button) button.disabled = true;
  showMessage('Verificando tus datos...', 'info');
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
    showToast('¡Bienvenido a RapiJob! Nos alegra tenerte aquí.', 'success');
    await loadServices();
  } catch (error) {
    showMessage(error.message || 'No se pudo iniciar sesión. Inténtalo nuevamente.', 'error');
  } finally {
    if (button) button.disabled = false;
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
    showToast('¡Bienvenido a RapiJob! Nos alegra tenerte aquí.', 'success');
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
  $('#loginForm')?.reset();
  $('#registerForm')?.reset();
  showMessage('', 'info');
  updateAuthUI();
  if (show) showToast('Has cerrado sesión correctamente. ¡Hasta pronto!', 'info');
  document.querySelector('#acceso')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
  const demoDate = $('#demoDate');
  const demoButton = $('#demoBookingBtn');
  const demoMessage = $('#demoBookingMessage');
  let demoTime = '';
  if (demoDate) {
    const today = new Date();
    const localToday = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
    demoDate.min = localToday;
    demoDate.value = localToday;
    const updateDemo = () => {
      demoButton.disabled = !(demoDate.value && demoTime && demoDate.value >= localToday);
      demoMessage.textContent = demoTime ? `Horario elegido: ${demoTime}. Pulsa el botón para ver el resumen.` : 'Selecciona uno de los horarios de ejemplo.';
      demoMessage.className = 'message info';
    };
    document.querySelectorAll('.demo-time').forEach((timeButton) => timeButton.addEventListener('click', () => {
      demoTime = timeButton.dataset.time;
      document.querySelectorAll('.demo-time').forEach((item) => item.classList.toggle('selected', item === timeButton));
      updateDemo();
    }));
    demoDate.addEventListener('change', updateDemo);
    demoButton.addEventListener('click', () => {
      if (!demoDate.value || !demoTime) return;
      const [year, month, day] = demoDate.value.split('-').map(Number);
      const dateLabel = new Date(year, month - 1, day).toLocaleDateString('es-PE', { dateStyle: 'long' });
      demoMessage.textContent = `Ejemplo de cita: ${dateLabel} a las ${demoTime}. Para reservar de verdad, inicia sesión y selecciona un horario publicado por un técnico.`;
      demoMessage.className = 'message success';
    });
  }
  $('#loginForm').addEventListener('submit', handleLogin);
  $('#registerForm').addEventListener('submit', handleRegister);
  $('#orderForm').addEventListener('submit', handleCreateOrder);
  $('#slotForm').addEventListener('submit', handleCreateSlot);
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
