// Global CSRF helper. Reads the token from the meta tag in base.html.
window.getCsrfToken = function () {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : "";
};
