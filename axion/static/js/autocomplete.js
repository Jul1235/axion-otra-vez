// static/js/autocomplete.js - Búsqueda en tiempo real

document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.querySelector('[data-autocomplete="product"]');
  if (!searchInput) return;

  // Crear contenedor de resultados
  let resultsContainer = document.getElementById('search-autocomplete-list');
  if (!resultsContainer) {
    resultsContainer = document.createElement('ul');
    resultsContainer.id = 'search-autocomplete-list';
    resultsContainer.className = 'autocomplete-results';
    resultsContainer.style.display = 'none';

    // Insertar después del input
    const wrapper = searchInput.parentElement;
    wrapper.style.position = 'relative';
    wrapper.appendChild(resultsContainer);
  }

  let debounceTimer;
  let currentFocus = -1;

  searchInput.addEventListener('input', function() {
    const query = this.value.trim();

    clearTimeout(debounceTimer);

    if (query.length < 2) {
      resultsContainer.style.display = 'none';
      resultsContainer.innerHTML = '';
      return;
    }

    debounceTimer = setTimeout(() => {
      fetch(`/api/search_autocomplete?q=${encodeURIComponent(query)}`)
      .then(response => response.json())
      .then(data => {
        resultsContainer.innerHTML = '';
        currentFocus = -1;

        if (data.length === 0) {
          resultsContainer.innerHTML = '<li class="autocomplete-item no-results">No se encontraron resultados</li>';
          resultsContainer.style.display = 'block';
          return;
        }

        data.forEach((item, index) => {
          const li = document.createElement('li');
          li.className = 'autocomplete-item';
          li.dataset.index = index;
          li.innerHTML = `
          <img src="${item.imagen ? '/static/' + item.imagen : 'https://via.placeholder.com/40x40?text=?'}"
          alt="${item.nombre}"
          onerror="this.src='https://via.placeholder.com/40x40?text=?'">
          <div class="item-info">
          <div class="item-name">${highlightMatch(item.nombre, query)}</div>
          <div class="item-price">$${item.precio.toFixed(2)}</div>
          ${item.categoria ? `<div class="item-category">${item.categoria}</div>` : ''}
          </div>
          `;

          li.addEventListener('click', function() {
            window.location.href = `/product/${item.id}`;
          });

          resultsContainer.appendChild(li);
        });

        resultsContainer.style.display = 'block';
      })
      .catch(error => {
        console.error('Error en autocomplete:', error);
        resultsContainer.style.display = 'none';
      });
    }, 300);
  });

  // Navegación con teclado
  searchInput.addEventListener('keydown', function(e) {
    const items = resultsContainer.querySelectorAll('.autocomplete-item:not(.no-results)');

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      currentFocus++;
      if (currentFocus >= items.length) currentFocus = 0;
      setActive(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      currentFocus--;
      if (currentFocus < 0) currentFocus = items.length - 1;
      setActive(items);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (currentFocus > -1 && items[currentFocus]) {
        items[currentFocus].click();
      }
    } else if (e.key === 'Escape') {
      resultsContainer.style.display = 'none';
    }
  });

  function setActive(items) {
    items.forEach((item, index) => {
      item.classList.remove('active');
      if (index === currentFocus) {
        item.classList.add('active');
        item.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  function highlightMatch(text, query) {
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return text.replace(regex, '<strong>$1</strong>');
  }

  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Cerrar al hacer clic fuera
  document.addEventListener('click', function(e) {
    if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
      resultsContainer.style.display = 'none';
    }
  });

  // Mantener abierto al hacer focus
  searchInput.addEventListener('focus', function() {
    if (resultsContainer.innerHTML && this.value.trim().length >= 2) {
      resultsContainer.style.display = 'block';
    }
  });
});
