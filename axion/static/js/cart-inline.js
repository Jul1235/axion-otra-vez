document.addEventListener('DOMContentLoaded', function() {
  // Interceptar clicks en botones 'add-to-cart' para confirmar inline
  document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const href = btn.getAttribute('href');
      if (!href) return;

      // Mostrar feedback inmediato
      showInlineConfirmation('Agregando al carrito...');

      fetch(href, { method: 'GET', credentials: 'same-origin' })
        .then(resp => {
          if (resp.ok) {
            // Incrementar contador visual del carrito si existe
            const cartCountEl = document.getElementById('cart-count');
            if (cartCountEl) {
              const val = parseInt(cartCountEl.textContent) || 0;
              cartCountEl.textContent = val + 1;
              // asegurarse que la insignia sea visible
              cartCountEl.style.display = '';
            }
            showInlineConfirmation('✓ Producto agregado al carrito');
          } else {
            showInlineConfirmation('Error al agregar al carrito', true);
          }
        }).catch(err => {
          console.error(err);
          showInlineConfirmation('Error de red', true);
        });
    });
  });

  function showInlineConfirmation(text, isError) {
    const containerId = 'inline-confirmations';
    let container = document.getElementById(containerId);
    if (!container) {
      container = document.createElement('div');
      container.id = containerId;
      container.style.position = 'fixed';
      container.style.right = '20px';
      container.style.bottom = '80px';
      container.style.zIndex = 1070;
      document.body.appendChild(container);
    }

    const card = document.createElement('div');
    card.className = 'card p-2 mb-2';
    card.style.minWidth = '220px';
    card.style.boxShadow = '0 6px 18px rgba(0,0,0,0.12)';
    card.innerHTML = `<div class="d-flex align-items-center"><div class="flex-grow-1">${escapeHtml(text)}</div><button class="btn-close ms-2" aria-label="cerrar"></button></div>`;
    if (isError) card.style.borderLeft = '4px solid #dc3545';
    else card.style.borderLeft = '4px solid #28a745';

    container.appendChild(card);

    // Close button
    card.querySelector('.btn-close').addEventListener('click', () => card.remove());

    setTimeout(() => {
      card.remove();
    }, 4500);
  }

  function escapeHtml(unsafe) {
    return unsafe.replace(/[&<>"'`]/g, function(m) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;', '`':'&#96;'})[m]; });
  }
});
