// static/js/wishlist.js
// Handle add/remove wishlist via AJAX and update UI in real-time.
document.addEventListener('DOMContentLoaded', function() {
  function updateWishlistCount(n) {
    // Update any visible wishlist counters on the page
    const targets = [
      document.getElementById('wishlist-count'),
      document.getElementById('sidebar-wishlist-count')
    ];
    targets.forEach(el => {
      if (!el) return;
      el.textContent = n;
      if (!n || Number(n) === 0) el.style.display = 'none'; else el.style.display = '';
    });
    // also update any badges with class 'wishlist-badge'
    document.querySelectorAll('.wishlist-badge').forEach(b => {
      b.textContent = n;
      if (!n || Number(n) === 0) b.style.display = 'none'; else b.style.display = '';
    });
  }

  async function sendAction(url) {
    const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!resp.ok) throw new Error('Network error ' + resp.status);
    return await resp.json();
  }

  function setButtonState(btn, inWishlist, newCount) {
    btn.dataset.inWishlist = inWishlist ? '1' : '0';
    btn.classList.toggle('in-wishlist', !!inWishlist);
    const icon = btn.querySelector('i');
    if (icon) {
      icon.className = inWishlist ? 'fas fa-heart' : 'far fa-heart';
      if (inWishlist) icon.style.color = ''; else icon.style.color = '';
    }
    if (typeof newCount !== 'undefined') updateWishlistCount(newCount);
  }

  function pulseButton(btn) {
    if (!btn) return;
    btn.classList.add('pulse');
    setTimeout(() => btn.classList.remove('pulse'), 700);
  }

  // No toast notifications for wishlist actions per user preference.

  document.body.addEventListener('click', function(e) {
    const btn = e.target.closest && e.target.closest('.btn-wishlist');
    if (!btn) return;
    e.preventDefault();

    const pid = btn.dataset.productId;
    const currently = btn.dataset.inWishlist === '1';

    (async () => {
      try {
        if (!currently) {
          const json = await sendAction(`/add_to_wishlist/${pid}`);
          setButtonState(btn, true, json.wishlist_count);
          pulseButton(btn);
          try { if (window.logUserAction) window.logUserAction({ action: 'wishlist_add', producto_id: pid, nombre: btn.dataset.productName || '', ts: new Date().toISOString() }); } catch(e){}
        } else {
          const json = await sendAction(`/remove_from_wishlist/${pid}`);
          setButtonState(btn, false, json.wishlist_count);
          pulseButton(btn);
          try { if (window.logUserAction) window.logUserAction({ action: 'wishlist_remove', producto_id: pid, nombre: btn.dataset.productName || '', ts: new Date().toISOString() }); } catch(e){}
        }
      } catch (err) {
        console.error('Wishlist action failed', err);
      }
    })();
  });
});
