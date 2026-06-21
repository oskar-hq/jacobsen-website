/*!
 * animations.js — Jacobsen Videoproduktion
 * Leichte Scroll-Reveals via IntersectionObserver.
 * Bewusst ohne GSAP/Lenis gehalten — native Scroll-Performance, nur ein paar dezente Effekte.
 */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var els = document.querySelectorAll('[data-reveal]');

  // Reduced-Motion oder kein IO-Support: alles sofort sichtbar zeigen
  if (reduce || !('IntersectionObserver' in window)) {
    for (var i = 0; i < els.length; i++) els[i].classList.add('in-view');
    return;
  }

  var io = new IntersectionObserver(function (entries, obs) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        obs.unobserve(entry.target); // nur einmal animieren
      }
    });
  }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 });

  els.forEach(function (el) { io.observe(el); });
})();
