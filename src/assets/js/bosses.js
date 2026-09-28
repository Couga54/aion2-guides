// World bosses: mark a kill, remember it in this browser, show when the boss can be up again
// (only for bosses whose respawn is known — data/bosses.json respawn_min).
(function () {
  'use strict';
  var page = document.querySelector('.bs-page');
  if (!page) return;
  var KEY = 'aion2-bosses-v1';
  var kills = {};
  try { kills = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { kills = {}; }
  var save = function () { try { localStorage.setItem(KEY, JSON.stringify(kills)); } catch (e) {} };

  var locale = page.dataset.lang === 'ru' ? 'ru-RU' : 'en-GB';
  var time = new Intl.DateTimeFormat(locale, { weekday: 'short', hour: '2-digit', minute: '2-digit' });
  var pad = function (n) { return (n < 10 ? '0' : '') + n; };
  var left = function (ms) {
    var m = Math.ceil(ms / 6e4);
    return Math.floor(m / 60) + ':' + pad(m % 60);
  };

  var items = [].slice.call(page.querySelectorAll('.bs-item'));
  function render() {
    var now = Date.now();
    items.forEach(function (li) {
      var at = kills[li.dataset.id];
      var status = li.querySelector('.bs-status');
      li.querySelector('.bs-undo').hidden = !at;
      li.classList.remove('is-dead', 'is-up');
      if (!at) { status.textContent = ''; return; }
      var text = page.dataset.tKilled + ' ' + time.format(at);
      var respawn = +li.dataset.respawn || 0;
      if (respawn) {
        var next = at + respawn * 6e4;
        if (next > now) { li.classList.add('is-dead'); text += ' · ' + page.dataset.tNext + ' ' + time.format(next) + ' (' + left(next - now) + ')'; }
        else { li.classList.add('is-up'); text += ' · ' + page.dataset.tUp; }
      }
      status.textContent = text;
    });
  }
  items.forEach(function (li) {
    li.querySelector('.bs-kill').addEventListener('click', function () { kills[li.dataset.id] = Date.now(); save(); render(); });
    li.querySelector('.bs-undo').addEventListener('click', function () { delete kills[li.dataset.id]; save(); render(); });
  });
  render();
  setInterval(render, 30000);
})();
