/*!
 * animations.js — Jacobsen Videoproduktion
 *  1) Leichte Scroll-Reveals (IntersectionObserver)
 *  2) Hero-"Assemble"-Intro (GSAP, einmal pro Session)
 *  2b) Kunden-Logo-Marquee (nahtlose Endlosschleife)
 *  3) Projekte: nativer Horizontal-Swipe (scroll-snap) + Fortschritt pro Panel
 *  4) Tab-/Filter-System (Leistung ↔ Beispiel-Video)
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
    var box = document.querySelector('.marquee');
    var track = document.querySelector('.marquee-track[data-marquee]');
    if (!box || !track || reduce || !track.children.length) return;

    // WICHTIG: erst nowrap-Layout aktivieren, dann messen (sonst zählt die umgebrochene Breite)
    track.classList.add('is-animated');

    var original = track.innerHTML;
    // 1) genug Kopien, bis EINE Hälfte mindestens die Bildschirmbreite füllt
    var safety = 0;
    while (track.scrollWidth < box.clientWidth && safety < 30) {
      track.innerHTML += original;
      safety++;
    }
    // 2) gefüllte Hälfte verdoppeln → nahtlose Endlosschleife bei translateX(-50%)
    var halfWidth = track.scrollWidth;
    track.innerHTML += track.innerHTML;

    // 3) konstante, ruhige Geschwindigkeit (~35px/s), unabhängig von Logo-Anzahl
    track.style.animationDuration = Math.max(30, Math.round(halfWidth / 35)) + 's';
  })();

  /* ---------- 3) „MEINE ARBEIT": SEGMENTED-SWITCHER + CAROUSEL ---------- */
  (function workSwitch() {
    var sw = document.querySelector('.switch');
    var carousel = document.querySelector('.work-carousel');
    var track = document.querySelector('.work-track');
    if (!sw || !carousel || !track) return;
    var pill = sw.querySelector('.switch-pill');
    var btns = [].slice.call(sw.querySelectorAll('.switch-btn'));
    var panels = [].slice.call(track.querySelectorAll('.work-panel'));
    if (!btns.length) return;
    var active = 0;

    function movePill() {
      var b = btns[active];
      pill.style.transform = 'translateX(' + b.offsetLeft + 'px)';
      pill.style.width = b.offsetWidth + 'px';
    }
    function setHeight() {
      if (panels[active]) carousel.style.height = panels[active].offsetHeight + 'px';
    }
    function setActive(i) {
      active = i;
      btns.forEach(function (b, idx) {
        var on = idx === i;
        b.classList.toggle('is-active', on);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      track.style.transform = 'translateX(' + (-i * (100 / btns.length)) + '%)';
      movePill();
      setHeight();
      // aktiven Button bei schmalem (scrollbarem) Switch in den Blick rücken
      if (btns[i].scrollIntoView) {
        btns[i].scrollIntoView({ inline: 'nearest', block: 'nearest' });
      }
    }

    btns.forEach(function (b, i) {
      b.addEventListener('click', function () { setActive(i); });
    });
    window.addEventListener('resize', function () { movePill(); setHeight(); });

    // Initiale Messung (auch nach Font-Load, damit Breiten stimmen)
    movePill(); setHeight();
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () { movePill(); setHeight(); });
    }
  })();

  /* ---------- 3b) VIDEOS: DSGVO-konformes Click-to-Load (youtube-nocookie) ---------- */
  (function videoLoad() {
    document.querySelectorAll('.video-embed').forEach(function (el) {
      el.addEventListener('click', function () {
        if (el.dataset.loaded) return;
        var id = el.getAttribute('data-id');
        if (!id) return;
        el.dataset.loaded = '1';
        var ifr = document.createElement('iframe');
        ifr.src = 'https://www.youtube-nocookie.com/embed/' + id +
                  '?autoplay=1&rel=0&modestbranding=1';
        ifr.title = el.getAttribute('data-title') || 'Video';
        ifr.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
        ifr.setAttribute('allowfullscreen', '');
        el.innerHTML = '';
        el.appendChild(ifr);
        // Höhe des Carousels ggf. neu setzen
        window.dispatchEvent(new Event('resize'));
      });
    });
  })();

  /* ---------- 4) TABS / FILTER (Leistung ↔ Beispiel-Video) ---------- */
  (function tabsFilter() {
    document.querySelectorAll('[role="tablist"]').forEach(function (list) {
      var tabs = [].slice.call(list.querySelectorAll('.tab'));
      if (!tabs.length) return;
      var container = list.parentElement;

      function activate(key) {
        tabs.forEach(function (t) {
          var on = t.getAttribute('data-tab') === key;
          t.classList.toggle('is-active', on);
          t.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        container.querySelectorAll(':scope > .tab-panel').forEach(function (panel) {
          panel.classList.toggle('is-active', panel.getAttribute('data-panel') === key);
        });
        // Fortschrittsbalken des nun sichtbaren Panels neu berechnen
        window.dispatchEvent(new Event('resize'));
      }

      tabs.forEach(function (t) {
        t.addEventListener('click', function () { activate(t.getAttribute('data-tab')); });
      });
    });
  })();
})();
