document.addEventListener('DOMContentLoaded', function() {
  // Solo inicializar si el navegador soporta EventSource
  if (!window.EventSource) return;

  // Crear contenedor de notificaciones en la UI
  function ensureContainer() {
    let c = document.getElementById('notifications-container');
    if (!c) {
      c = document.createElement('div');
      c.id = 'notifications-container';
      c.style.position = 'fixed';
      c.style.right = '20px';
      c.style.bottom = '20px';
      c.style.zIndex = 1060;
      document.body.appendChild(c);
    }
    return c;
  }

  const container = ensureContainer();
  const es = new EventSource('/notifications/stream');

  es.onmessage = function(evt) {
    try {
      const payload = JSON.parse(evt.data);
      const msg = payload.message || 'Notificación';
      showNotification(msg);
    } catch (e) {
      console.error('Invalid SSE payload', e);
    }
  };

  es.onerror = function(err) {
    // reconectar automático por EventSource; mostrar estado
    console.warn('SSE connection error', err);
  };

  function showNotification(text) {
    const card = document.createElement('div');
    card.className = 'card shadow-sm mb-2';
    card.style.minWidth = '260px';
    card.innerHTML = `<div class="card-body p-2"><small class="text-muted">Notificación</small><div>${escapeHtml(text)}</div></div>`;
    container.appendChild(card);
    // Mostrar por menos tiempo para una experiencia menos intrusiva
    setTimeout(() => {
      card.classList.add('fade-out');
      setTimeout(() => card.remove(), 300);
    }, 3000);
  }

  function escapeHtml(unsafe) {
    return unsafe.replace(/[&<>"'`]/g, function(m) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;', '`':'&#96;'})[m]; });
  }

});
