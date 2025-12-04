document.addEventListener('DOMContentLoaded', function() {
  // Interceptar clicks en botones 'add-to-cart' para confirmar inline
  document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const href = btn.getAttribute('href');
      const img = btn.dataset.image || null;
      if (!href) return;

      // Mostrar feedback inmediato (se posicionará sobre el botón)
      showInlineConfirmation('Agregando al carrito...', false, null, btn);

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
              // Update stock counts for this product (if present on page)
              try {
                const pid = btn.dataset.productId || btn.getAttribute('data-product-id');
                if (pid) {
                  document.querySelectorAll(`[data-stock-product-id="${pid}"]`).forEach(el => {
                    const countEl = el.querySelector('.stock-count');
                    if (!countEl) return;
                    let cur = parseInt(countEl.textContent) || 0;
                    if (cur > 0) cur = cur - 1;
                    // Update display and classes
                    if (cur <= 0) {
                      // Replace with an AGOTADO badge
                      el.innerHTML = '<span class="badge bg-danger">AGOTADO</span>';
                    } else {
                      // adjust style based on thresholds
                      const parent = countEl.parentElement;
                      countEl.textContent = cur;
                      if (cur <= 5) {
                        parent.classList.remove('text-success','text-warning');
                        parent.classList.add('text-danger');
                      } else if (cur <= 10) {
                        parent.classList.remove('text-success','text-danger');
                        parent.classList.add('text-warning');
                      } else {
                        parent.classList.remove('text-warning','text-danger');
                        parent.classList.add('text-success');
                      }
                    }
                  });

                  // disable add-to-cart buttons for this product if none left
                  const newStockEl = document.querySelector(`[data-stock-product-id="${pid}"] .stock-count`);
                  const newStock = newStockEl ? parseInt(newStockEl.textContent) || 0 : 0;
                  if (newStock <= 0) {
                    document.querySelectorAll(`.add-to-cart-btn[data-product-id="${pid}"]`).forEach(b => {
                      try { b.classList.remove('btn-primary-custom'); b.classList.add('btn-secondary'); b.setAttribute('disabled','disabled'); b.innerHTML = '<i class="fas fa-ban"></i> No Disponible'; } catch(e){}
                    });
                  }
                }
              } catch (e) { console.warn('Could not update stock UI', e); }

                // Log action (client-side) if available
                try {
                  const pid = btn.dataset.productId || btn.getAttribute('data-product-id');
                  const pname = btn.dataset.productName || btn.getAttribute('data-product-name') || '';
                  if (window.logUserAction) window.logUserAction({ action: 'agregar', producto_id: pid, nombre: pname, ts: new Date().toISOString() });
                } catch (e) {}

                // Show a short confirmation with image (if available) over the button
                showInlineConfirmation('Se agregó un producto al carrito', false, img, btn);
          } else {
              // log failed
              try { const pid = btn.dataset.productId || btn.getAttribute('data-product-id'); if (window.logUserAction) window.logUserAction({ action: 'agregar_fallo', producto_id: pid, ts: new Date().toISOString() }); } catch(e){}
              showInlineConfirmation('Error al agregar al carrito', true, null, btn);
          }
        }).catch(err => {
          console.error(err);
            try { const pid = btn.dataset.productId || btn.getAttribute('data-product-id'); if (window.logUserAction) window.logUserAction({ action: 'agregar_fallo', producto_id: pid, ts: new Date().toISOString() }); } catch(e){}
            showInlineConfirmation('Error de red', true, null, btn);
        });
    });
  });

    // Toggle inline product description when clicking the card (but not on buttons/links)
    document.body.addEventListener('click', function(e) {
      const card = e.target.closest && e.target.closest('.product-card');
      if (!card) return;
      // Ignore clicks on anchors and buttons inside the card
      if (e.target.closest('a') || e.target.closest('button') || e.target.closest('.btn-wishlist')) return;
      const desc = card.querySelector('.product-desc');
      if (desc) {
        if (desc.style.display === 'none' || getComputedStyle(desc).display === 'none') {
          desc.style.display = 'block';
          desc.style.opacity = 0;
          desc.style.transition = 'opacity 220ms ease';
          requestAnimationFrame(() => desc.style.opacity = 1);
        } else {
          desc.style.opacity = 0;
          setTimeout(() => { desc.style.display = 'none'; }, 220);
        }
      }
    });

  function showInlineConfirmation(text, isError, imageUrl, targetBtn) {
    // Create a small overlay positioned near the target button (centered above it when possible)
    const overlay = document.createElement('div');
    overlay.className = 'inline-confirm-overlay card p-2 d-inline-confirmation';
    overlay.style.position = 'fixed';
    overlay.style.zIndex = 2100;
    overlay.style.minWidth = '160px';
    overlay.style.maxWidth = '320px';
    overlay.style.boxShadow = '0 6px 18px rgba(0,0,0,0.12)';
    overlay.style.overflow = 'hidden';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.gap = '8px';

    if (isError) overlay.style.borderLeft = '4px solid #dc3545';
    else overlay.style.borderLeft = '4px solid #28a745';

    let inner = '';
    if (imageUrl) {
      inner += `<div style="width:44px;height:30px;flex:0 0 auto;">
                  <img src="${escapeHtml(imageUrl)}" style="width:100%;height:100%;object-fit:cover;border-radius:4px;" onerror="this.src='https://via.placeholder.com/56x40?text=?'" />
                </div>`;
    }
    inner += `<div style="flex:1 1 auto;">
                <div class="confirm-text small">${escapeHtml(text)}</div>
             </div>`;
    overlay.innerHTML = inner;

    document.body.appendChild(overlay);

    // Position overlay centered above the target button when possible
    function positionOverlay() {
      try {
        const rect = (targetBtn && targetBtn.getBoundingClientRect && targetBtn.getBoundingClientRect()) || { left: window.innerWidth/2, top: window.innerHeight/2, width: 0, height: 0 };
        const ow = overlay.offsetWidth;
        const oh = overlay.offsetHeight;
        let left = rect.left + (rect.width / 2) - (ow / 2);
        let top = rect.top - oh - 8;
        // if not enough space above, place below the button
        if (top < 8) top = rect.bottom + 8;
        // keep within viewport
        if (left < 8) left = 8;
        if (left + ow > window.innerWidth - 8) left = window.innerWidth - ow - 8;
        overlay.style.left = Math.round(left) + 'px';
        overlay.style.top = Math.round(top) + 'px';
      } catch (e) {
        overlay.style.right = '20px';
        overlay.style.bottom = '80px';
      }
    }

    // initial position after appended
    requestAnimationFrame(positionOverlay);
    // reposition on resize/scroll briefly
    const ro = () => positionOverlay();
    window.addEventListener('resize', ro);
    window.addEventListener('scroll', ro, { passive: true });

    // Create icon element to swap after brief delay
    const iconEl = document.createElement('div');
    iconEl.style.opacity = 0;
    iconEl.style.transition = 'opacity 220ms ease';

    const showSuccess = !isError;

    // After 700ms fade to icon
    setTimeout(() => {
      // fade text
      const textEl = overlay.querySelector('.confirm-text');
      if (textEl) { textEl.style.transition = 'opacity 200ms ease'; textEl.style.opacity = 0; }
      setTimeout(() => {
        iconEl.innerHTML = showSuccess ? '<i class="fas fa-check-circle" style="color:#28a745;font-size:1.2rem"></i>' : '<i class="fas fa-times-circle" style="color:#dc3545;font-size:1.2rem"></i>';
        overlay.insertBefore(iconEl, overlay.firstChild);
        iconEl.style.opacity = 1;
      }, 200);
    }, 700);

    // After 3000ms remove overlay and listeners
    setTimeout(() => {
      try { iconEl.style.opacity = 0; } catch(e){}
      try { overlay.remove(); } catch(e){}
      window.removeEventListener('resize', ro);
      window.removeEventListener('scroll', ro);
    }, 3000);
  }

  function escapeHtml(unsafe) {
    return unsafe.replace(/[&<>"'`]/g, function(m) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;', '`':'&#96;'})[m]; });
  }
});
