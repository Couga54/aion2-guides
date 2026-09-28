(function () {
  'use strict';
  var root = document.documentElement;
  var OFF = (root.getAttribute('data-off') || '').split(' ');
  var MODES = ['pve', 'pvp', 'lvl'].filter(function (m) { return OFF.indexOf(m) < 0; });

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (e) { return null; }
  }

  // ---- theme -------------------------------------------------------------
  var themeBtn = document.querySelector('.theme-toggle');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var dark = root.dataset.theme ? root.dataset.theme === 'dark' : !matchMedia('(prefers-color-scheme: light)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    store('theme', root.dataset.theme);
  });

  // ---- class picker: close on outside click and Escape --------------------
  var cmenu = document.querySelector('.class-menu');
  var calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (cmenu) {
    // <details> closes instantly, so play the closing animation first.
    var closeMenu = function () {
      if (!cmenu.open || cmenu.classList.contains('is-closing')) return;
      if (calm) { cmenu.open = false; return; }
      cmenu.classList.add('is-closing');
      setTimeout(function () { cmenu.open = false; cmenu.classList.remove('is-closing'); }, 160);
    };
    cmenu.querySelector('summary').addEventListener('click', function (ev) {
      if (cmenu.open) { ev.preventDefault(); closeMenu(); }
    });
    document.addEventListener('click', function (ev) { if (cmenu.open && !cmenu.contains(ev.target)) closeMenu(); });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && cmenu.open) { closeMenu(); cmenu.querySelector('summary').focus(); }
    });
  }

  // ---- what's new: the latest entry pops up once; the "?" button leads to the changelog page ----
  var wn = document.querySelector('.whatsnew');
  var top = document.querySelector('.wn-top');
  var latest = wn ? wn.dataset.id : null;
  // Opening the changelog page counts as having seen the latest entry.
  var clPage = document.querySelector('[data-changelog-seen]');
  if (clPage) store('whatsnew-seen', clPage.dataset.changelogSeen);
  var markDot = function () { if (top) top.classList.toggle('has-new', !!latest && store('whatsnew-seen') !== latest); };
  if (wn && typeof wn.showModal === 'function') {
    var seen = function () { store('whatsnew-seen', latest); markDot(); };
    wn.addEventListener('close', seen);
    // A link inside the dialog navigates away — count that as seen too.
    wn.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', seen); });
    // Click on the backdrop closes it.
    wn.addEventListener('click', function (ev) { if (ev.target === wn) wn.close(); });
    if (!clPage && store('whatsnew-seen') !== latest) setTimeout(function () { if (!wn.open) wn.showModal(); }, 600);
  }
  markDot();

  // ---- language: remember the choice, keep ?mode and #section ------------
  store('lang', root.lang);
  document.querySelectorAll('[data-keep-query]').forEach(function (a) {
    a.addEventListener('click', function () {
      store('lang', a.getAttribute('hreflang'));
      a.href = a.href.split(/[?#]/)[0] + location.search + location.hash;
    });
  });

  // ---- launch schedule timers (home) ---------------------------------------
  var evBox = document.querySelector('.events');
  if (evBox) {
    var evs = [].slice.call(evBox.querySelectorAll('.ev[data-at]')).map(function (li) {
      return { li: li, at: Date.parse(li.dataset.at), cells: li.querySelectorAll('.ev-timer b') };
    });
    var pad = function (n) { return (n < 10 ? '0' : '') + n; };
    // Main date = the visitor's own local time; the UTC text from the build moves to the note.
    try {
      var fmt = new Intl.DateTimeFormat(evBox.dataset.lang === 'ru' ? 'ru-RU' : 'en-GB',
        { weekday: 'short', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' });
      evs.forEach(function (e) {
        var t = e.li.querySelector('.ev-when time'), el = e.li.querySelector('.ev-local');
        if (!t || !el) return;
        el.textContent = t.textContent;
        t.textContent = fmt.format(e.at);
      });
    } catch (err) {}
    var tick = function () {
      var now = Date.now(), next = null;
      evs.forEach(function (e) {
        var ms = e.at - now;
        e.li.classList.toggle('is-done', ms <= 0);
        e.li.classList.remove('is-next');
        if (ms <= 0) return;
        if (!next) next = e;
        var v = [Math.floor(ms / 864e5), Math.floor(ms / 36e5) % 24, Math.floor(ms / 6e4) % 60, Math.floor(ms / 1e3) % 60];
        for (var i = 0; i < 4; i++) e.cells[i].textContent = i ? pad(v[i]) : v[i];
      });
      if (next) {
        next.li.classList.add('is-next');
        setTimeout(tick, 1000 - (Date.now() % 1000));
      }
    };
    tick();
  }

  // Everything below is for class pages.
  if (!document.querySelector('.guide')) return;

  // ---- table of contents (rebuilt per mode) --------------------------------
  var sideToc = document.querySelector('.toc-list');
  var mobileToc = document.querySelector('.toc-mobile');
  var observer = null;

  function visibleSections() {
    return Array.prototype.filter.call(document.querySelectorAll('.guide .g-section'), function (s) {
      return s.offsetParent !== null;
    });
  }
  function buildToc() {
    var secs = visibleSections();
    [sideToc, mobileToc].forEach(function (nav) {
      if (!nav) return;
      nav.textContent = '';
      secs.forEach(function (s) {
        var a = document.createElement('a');
        a.href = '#' + s.id;
        a.textContent = s.querySelector('h2').textContent;
        nav.appendChild(a);
      });
    });
    if (observer) observer.disconnect();
    if (!('IntersectionObserver' in window)) return;
    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        document.querySelectorAll('.toc-list a, .toc-mobile a').forEach(function (a) {
          var on = a.hash === '#' + e.target.id;
          if (on) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
          if (on && a.parentNode === mobileToc) {
            // keep the active chip visible without scrolling the page
            if (a.offsetLeft < mobileToc.scrollLeft || a.offsetLeft + a.offsetWidth > mobileToc.scrollLeft + mobileToc.clientWidth) {
              mobileToc.scrollLeft = a.offsetLeft - 16;
            }
          }
        });
      });
    }, { rootMargin: '-35% 0px -60% 0px' });
    secs.forEach(function (s) { observer.observe(s); });
  }

  // ---- mode switch -----------------------------------------------------------
  var modeButtons = document.querySelectorAll('.mode-switch [data-set-mode]');
  function syncButtons(mode) {
    mode = mode || root.dataset.mode;
    modeButtons.forEach(function (b) { b.setAttribute('aria-checked', String(b.dataset.setMode === mode)); });
  }
  var guide = document.querySelector('.guide');
  var switchTimer = null, target = null;
  function setMode(mode) {
    if (MODES.indexOf(mode) < 0 || mode === (target || root.dataset.mode)) return;
    if (calm) return applyMode(mode);
    target = mode;
    // Fade the guide out, swap the mode (the hero animates in CSS), fade back in.
    syncButtons(mode);
    guide.classList.add('is-switching');
    clearTimeout(switchTimer);
    switchTimer = setTimeout(function () {
      target = null;
      applyMode(mode);
      guide.classList.remove('is-switching');
    }, 160);
  }
  function applyMode(mode) {
    var y = window.scrollY;              // keep the page exactly where it is
    root.dataset.mode = mode;
    window.scrollTo({ top: y, behavior: 'instant' });
    syncButtons();
    buildToc();
    store('mode', mode);
    var url = new URL(location.href);
    if (mode === 'pve') url.searchParams.delete('mode'); else url.searchParams.set('mode', mode);
    var anchor = url.hash && document.getElementById(url.hash.slice(1));
    if (anchor && !anchor.offsetParent) url.hash = '';
    history.replaceState(null, '', url);
  }
  modeButtons.forEach(function (b) {
    b.addEventListener('click', function () { setMode(b.dataset.setMode); });
    b.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      e.preventDefault();
      var i = MODES.indexOf(target || root.dataset.mode) + (e.key === 'ArrowRight' ? 1 : -1);
      var next = MODES[(i + MODES.length) % MODES.length];
      setMode(next);
      document.querySelector('.mode-switch [data-set-mode="' + next + '"]').focus();
    });
  });
  // In-text links to another mode open that guide from the top.
  document.querySelectorAll('.guide [data-set-mode]').forEach(function (b) {
    b.addEventListener('click', function () { setMode(b.dataset.setMode); window.scrollTo({ top: 0, behavior: 'instant' }); });
  });

  // A link to a section of another mode switches to that mode.
  var hashTarget = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  var scope = hashTarget && hashTarget.closest('[data-only]');
  if (scope && scope.dataset.only.split(' ').indexOf(root.dataset.mode) < 0) {
    var alt = scope.dataset.only.split(' ').filter(function (m) { return MODES.indexOf(m) >= 0; })[0];
    if (alt) root.dataset.mode = alt;
  }
  syncButtons();
  buildToc();
  // Turn on the mode transitions only after the first paint, so the page doesn't animate on load.
  requestAnimationFrame(function () { requestAnimationFrame(function () { root.classList.add('anim'); }); });
  if (hashTarget) window.addEventListener('load', function () { hashTarget.scrollIntoView({ behavior: 'instant' }); });

  // ---- leveling tracker --------------------------------------------------
  var tracker = document.querySelector('.tracker');
  if (tracker) {
    var key = 'lvl-progress:' + tracker.dataset.class;
    var done = {};
    try { done = JSON.parse(store(key) || '{}') || {}; } catch (e) { done = {}; }
    var boxes = tracker.querySelectorAll('input[data-step]');
    var bar = tracker.querySelector('.progress');
    var render = function () {
      var n = 0;
      boxes.forEach(function (b) {
        b.checked = !!done[b.dataset.step];
        b.closest('.step').classList.toggle('done', b.checked);
        if (b.checked) n++;
      });
      bar.querySelector('span').style.width = (boxes.length ? (100 * n / boxes.length) : 0) + '%';
      bar.setAttribute('aria-valuenow', n);
      tracker.querySelector('.progress-count').textContent = n;
    };
    boxes.forEach(function (b) {
      b.addEventListener('change', function () {
        if (b.checked) done[b.dataset.step] = 1; else delete done[b.dataset.step];
        store(key, JSON.stringify(done));
        render();
      });
    });
    tracker.querySelector('.tracker-reset').addEventListener('click', function (e) {
      if (!confirm(e.currentTarget.dataset.confirm)) return;
      done = {};
      store(key, '{}');
      render();
    });
    render();
  }
})();
