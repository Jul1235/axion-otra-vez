// password-toggle.js
document.addEventListener('DOMContentLoaded', function () {
  // Attach event via delegation to support dynamic fields if needed
  document.querySelectorAll('.password-toggle').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      var wrapper = btn.closest('.password-wrapper');
      if (!wrapper) return;
      var input = wrapper.querySelector('.password-input');
      if (!input) return;

      var isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';

      // Update icon if using FontAwesome
      var icon = btn.querySelector('i');
      if (icon) {
        // support fa / fas / fa-solid classes
        if (isPassword) {
          icon.classList.remove('fa-eye');
          icon.classList.add('fa-eye-slash');
        } else {
          icon.classList.remove('fa-eye-slash');
          icon.classList.add('fa-eye');
        }
      }

      // Update aria attributes
      btn.setAttribute('aria-pressed', isPassword ? 'true' : 'false');
      btn.setAttribute('aria-label', isPassword ? 'Ocultar contraseña' : 'Mostrar contraseña');
    });
  });
});
