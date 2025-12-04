// static/js/autocomplete.js - Búsqueda en tiempo real

document.addEventListener('DOMContentLoaded', function() {
  // Simple behavior: no real-time search. When user presses Enter, perform a search.
  const searchInput = document.querySelector('[data-autocomplete="product"]');
  if (!searchInput) return;

  // If the input is inside a form, prefer submitting the form on Enter.
  searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      const q = this.value.trim();
      // Redirect to the main listing page with the search query
      window.location.href = `/home?search=${encodeURIComponent(q)}`;
    }
  });

  // Remove any visual autocomplete UI that might remain
  const existing = document.getElementById('search-autocomplete-list');
  if (existing) existing.remove();
});
