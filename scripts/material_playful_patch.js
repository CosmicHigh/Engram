/* engram-playful-hero-v2 — hero discovery, value bursts and tap confetti */
(function () {
  'use strict';

  if (window.__engramPlayfulHeroV2) return;
  window.__engramPlayfulHeroV2 = true;

  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var markFrame = 0;

  function directStats(group) {
    return Array.prototype.filter.call(group.children, function (child) {
      return child.classList && child.classList.contains('stat');
    });
  }

  function firstMetricGroup(screen) {
    var groups = screen.querySelectorAll('.stat-grid, .dual');
    for (var index = 0; index < groups.length; index += 1) {
      if (directStats(groups[index]).length) return groups[index];
    }
    return null;
  }

  function restartClass(element, className, duration) {
    if (!element || reduceMotion) return;
    element.classList.remove(className);
    void element.offsetWidth;
    element.classList.add(className);
    window.setTimeout(function () {
      element.classList.remove(className);
    }, duration || 760);
  }

  function bindValueAnimation(value) {
    if (!value || value.dataset.m3HeroValueReady) return;
    value.dataset.m3HeroValueReady = 'true';

    var previous = value.textContent;
    new MutationObserver(function () {
      var next = value.textContent;
      if (next === previous) return;
      previous = next;
      var card = value.closest('.m3-hero-card');
      if (!card) return;
      restartClass(card, 'm3-value-burst', 780);
      try {
        if (navigator.vibrate) navigator.vibrate([8, 18, 10]);
      } catch (error) { /* optional enhancement */ }
    }).observe(value, {
      childList: true,
      characterData: true,
      subtree: true
    });
  }

  function markHeroes() {
    document.querySelectorAll('.screen').forEach(function (screen) {
      var group = firstMetricGroup(screen);
      if (!group) return;

      group.classList.add('m3-hero-grid');
      directStats(group).forEach(function (card, index) {
        card.classList.add('m3-hero-card');
        card.style.setProperty('--hero-index', String(index));
        var value = card.querySelector('.v');
        if (value) bindValueAnimation(value);
      });
    });
  }

  function scheduleMark() {
    if (markFrame) return;
    markFrame = window.requestAnimationFrame(function () {
      markFrame = 0;
      markHeroes();
    });
  }

  function replayActiveHeroes() {
    if (reduceMotion) return;
    window.setTimeout(function () {
      var active = document.querySelector('.screen.active');
      if (!active) return;
      active.querySelectorAll('.m3-hero-card').forEach(function (card, index) {
        window.setTimeout(function () {
          restartClass(card, 'm3-hero-replay', 900);
          var value = card.querySelector('.v');
          if (value) {
            value.style.animation = 'none';
            void value.offsetWidth;
            value.style.animation = '';
          }
        }, index * 55);
      });
    }, 24);
  }

  function sparkBurst(card, clientX, clientY) {
    if (reduceMotion) return;
    var rect = card.getBoundingClientRect();
    var originX = clientX ? clientX - rect.left : rect.width / 2;
    var originY = clientY ? clientY - rect.top : rect.height / 2;
    var count = 11;

    for (var index = 0; index < count; index += 1) {
      var spark = document.createElement('span');
      var angle = (Math.PI * 2 * index / count) - Math.PI / 2;
      var distance = 42 + (index % 4) * 9;
      spark.className = 'm3-spark';
      spark.style.left = originX + 'px';
      spark.style.top = originY + 'px';
      spark.style.setProperty('--spark-x', Math.cos(angle) * distance + 'px');
      spark.style.setProperty('--spark-y', Math.sin(angle) * distance + 'px');
      spark.style.setProperty('--spark-r', (110 + index * 47) + 'deg');
      spark.style.animationDelay = (index % 3) * 18 + 'ms';
      card.appendChild(spark);
      spark.addEventListener('animationend', function (event) {
        event.currentTarget.remove();
      }, { once: true });
    }
  }

  function playfulTap(event) {
    var card = event.target.closest && event.target.closest('.m3-hero-card');
    if (!card) return;
    restartClass(card, 'm3-wiggle', 680);
    sparkBurst(card, event.clientX, event.clientY);
    try {
      if (navigator.vibrate) navigator.vibrate([11, 24, 8]);
    } catch (error) { /* optional enhancement */ }
  }

  function bindNavigationReplay() {
    document.querySelectorAll('.nav-btn').forEach(function (button) {
      if (button.dataset.m3HeroReplayReady) return;
      button.dataset.m3HeroReplayReady = 'true';
      button.addEventListener('click', replayActiveHeroes);
    });
  }

  function initialisePlayfulLayer() {
    markHeroes();
    bindNavigationReplay();
    replayActiveHeroes();

    document.addEventListener('pointerdown', playfulTap, { passive: true });

    new MutationObserver(function (mutations) {
      var shouldMark = false;
      var shouldReplay = false;

      mutations.forEach(function (mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length) {
          shouldMark = true;
        }
        if (mutation.type === 'attributes' &&
            mutation.target.classList &&
            mutation.target.classList.contains('screen') &&
            mutation.target.classList.contains('active')) {
          shouldReplay = true;
        }
      });

      if (shouldMark) scheduleMark();
      if (shouldReplay) replayActiveHeroes();
      bindNavigationReplay();
    }).observe(document.body, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['class']
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialisePlayfulLayer, { once: true });
  } else {
    initialisePlayfulLayer();
  }
})();
