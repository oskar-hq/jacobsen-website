/*!
 * animations.js — Jacobsen Videoproduktion
 *  1) Leichte Scroll-Reveals (IntersectionObserver)
 *  2) Hero-"Assemble"-Intro (GSAP, einmal pro Session)
 *  3) Horizontaler Projekte-Scroll
 *       Desktop (Pointer fein, ≥1000px): GSAP-ScrollTrigger-Pin (vertikal → horizontal)
 *       Mobile/Touch: nativer Swipe mit CSS scroll-snap
 *  prefers-reduced-motion wird überall respektiert.
 */
(function () {
  'use strict';

  var reduce  = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var gsap    = window.gsap;
  var hasGSAP = typeof gsap !== 'undefined';

  /* ---------- 1) SCROLL-REVEALS ---------- */
  (function reveals() {
    var els = document.querySelectorAll('[data-reveal]');
    if (reduce || !('IntersectionObserver' in window)) {
      for (var i = 0; i < els.length; i++) els[i].classList.add('in-view');
      return;
    }
    var io = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in-view'); obs.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 });
    els.forEach(function (el) { io.observe(el); });
  })();

  /* ---------- 2) HERO "ASSEMBLE" ---------- */
  (function heroAssemble() {
    var h1 = document.querySelector('.hero-name');
    if (!h1) return;

    // Buchstaben in Spans verpacken (Screenreader liest weiterhin aria-label="Jacobsen")
    var text = h1.textContent.trim();
    h1.textContent = '';
    var letters = [];
    for (var i = 0; i < text.length; i++) {
      var s = document.createElement('span');
      s.className = 'hero-letter';
      s.setAttribute('aria-hidden', 'true');
      s.textContent = text.charAt(i);
      h1.appendChild(s);
      letters.push(s);
    }

    var done = false;
    try { done = sessionStorage.getItem('heroIntroDone') === '1'; } catch (e) {}

    // Endzustand sofort, wenn kein Effekt gewünscht/möglich
    if (reduce || !hasGSAP || done) return;

    // Startzustand sofort setzen (vermeidet Aufblitzen des fertigen Schriftzugs)
    gsap.set(letters, {
      opacity: 0,
      x: function () { return Math.random() * 60 - 30; },   // ±30px
      y: function () { return Math.random() * 50 - 25; },   // ±25px
      rotation: function () { return Math.random() * 16 - 8; }
    });
    gsap.set(h1, { filter: 'blur(5px)' });

    function play() {
      gsap.timeline({
        onComplete: function () {
          gsap.set(letters, { clearProps: 'transform,opacity' });
          gsap.set(h1, { clearProps: 'filter' });
          try { sessionStorage.setItem('heroIntroDone', '1'); } catch (e) {}
        }
      })
      .to(h1, { filter: 'blur(0px)', duration: 0.7, ease: 'power2.out' }, 0)
      .to(letters, {
        opacity: 1, x: 0, y: 0, rotation: 0,
        duration: 0.8, ease: 'back.out(1.7)', stagger: 0.05
      }, 0);
    }

    // Erst nach Font-Load starten (kein Layout-Shift)
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(play);
    else play();
  })();

  /* ---------- 2b) KUNDEN-LOGO-MARQUEE ---------- */
  (function marquee() {
    var track = document.querySelector('.marquee-track[data-marquee]');
    if (!track || reduce) return;            // reduced-motion: statische, umgebrochene Reihe
    if (!track.children.length) return;
    // Logo-Set duplizieren → nahtlose Endlosschleife (translateX -50%)
    track.innerHTML = track.innerHTML + track.innerHTML;
    track.classList.add('is-animated');
  })();

  /* ---------- 3) HORIZONTALER PROJEKTE-SCROLL ---------- */
  (function horizontal() {
    var section = document.querySelector('.portfolio');
    var hscroll = document.querySelector('.portfolio-hscroll');
    var track   = document.querySelector('.portfolio-track');
    var bar     = document.querySelector('.portfolio-progress-bar');
    if (!section || !hscroll || !track) return;

    function setProgress(p) {
      if (!bar) return;
      p = Math.max(0, Math.min(1, p));
      var range = bar.parentElement.clientWidth - bar.offsetWidth;
      bar.style.transform = 'translateX(' + (p * range) + 'px)';
    }

    var desktopPin = !reduce && hasGSAP &&
      window.matchMedia('(min-width: 1000px) and (pointer: fine)').matches;

    if (desktopPin) {
      // Desktop: vertikales Scrollen → horizontaler Tween, Sektion gepinnt
      gsap.registerPlugin(ScrollTrigger);
      section.classList.add('is-hpin');
      gsap.to(track, {
        x: function () { return -(track.scrollWidth - hscroll.clientWidth); },
        ease: 'none',
        scrollTrigger: {
          trigger: section,
          start: 'top top',
          end: function () { return '+=' + (track.scrollWidth - hscroll.clientWidth); },
          pin: true,
          scrub: 0.6,
          anticipatePin: 1,
          invalidateOnRefresh: true,
          onUpdate: function (self) { setProgress(self.progress); }
        }
      });
      window.addEventListener('load', function () { ScrollTrigger.refresh(); });
    } else {
      // Mobile/Touch (& reduced): nativer Swipe, Fortschritt aus scrollLeft
      var update = function () {
        var max = hscroll.scrollWidth - hscroll.clientWidth;
        setProgress(max > 0 ? hscroll.scrollLeft / max : 0);
      };
      hscroll.addEventListener('scroll', update, { passive: true });
      window.addEventListener('resize', update);
      update();
    }
  })();
})();
