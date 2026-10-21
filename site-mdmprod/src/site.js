(function () {
  var btn = document.getElementById('menu-btn');
  var menu = document.getElementById('menu');
  if (!btn || !menu) return;
  function close() {
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-label', 'Ouvrir le menu');
  }
  btn.addEventListener('click', function () {
    var open = menu.hidden;
    menu.hidden = !open;
    btn.setAttribute('aria-expanded', String(open));
    btn.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
  });
  menu.addEventListener('click', function (e) { if (e.target.closest('a')) close(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !menu.hidden) { close(); btn.focus(); } });
})();
