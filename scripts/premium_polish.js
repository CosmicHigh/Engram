/* engram-premium-polish-v3 */
(function () {
  'use strict';

  if (window.__engramPremiumPolishV3) return;
  window.__engramPremiumPolishV3 = true;

  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var decorateFrame = 0;

  function activeScreen() {
    return document.querySelector('.screen.active');
  }

  function restart(element, className, duration) {
    if (!element || reduceMotion) return;
    element.classList.remove(className);
    void element.offsetWidth;
    element.classList.add(className);
    window.setTimeout(function () {
      element.classList.remove(className);
    }, duration || 760);
  }

  function createLayer(className) {
    var layer = document.createElement('span');
    layer.className = 'm3-premium-layer ' + className;
    layer.setAttribute('aria-hidden', 'true');
    return layer;
  }

  function bindPremiumCard(card) {
    if (!card || card.dataset.m3PremiumReady) return;
    card.dataset.m3PremiumReady = 'true';
    card.classList.add('m3-premium-card');

    card.insertBefore(createLayer('m3-premium-grid'), card.firstChild);
    card.insertBefore(createLayer('m3-premium-mesh'), card.firstChild);
    card.insertBefore(createLayer('m3-premium-shine'), card.firstChild);

    var frame = 0;
    var latest = null;

    function applyPointer() {
      frame = 0;
      if (!latest) return;
      var rect = card.getBoundingClientRect();
      var x = Math.max(0, Math.min(1, (latest.clientX - rect.left) / rect.width));
      var y = Math.max(0, Math.min(1, (latest.clientY - rect.top) / rect.height));
      card.style.setProperty('--px', (x * 100).toFixed(1) + '%');
      card.style.setProperty('--py', (y * 100).toFixed(1) + '%');
      card.style.setProperty('--tilt-x', ((x - .5) * 8).toFixed(2) + 'deg');
      card.style.setProperty('--tilt-y', ((.5 - y) * 7).toFixed(2) + 'deg');
      card.style.setProperty('--lift', '-3px');
    }

    function move(event) {
      if (reduceMotion) return;
      latest = event;
      card.classList.add('m3-tilt-active');
      if (!frame) frame = window.requestAnimationFrame(applyPointer);
    }

    function reset() {
      latest = null;
      card.classList.remove('m3-tilt-active');
      card.style.setProperty('--px', '50%');
      card.style.setProperty('--py', '35%');
      card.style.setProperty('--tilt-x', '0deg');
      card.style.setProperty('--tilt-y', '0deg');
      card.style.setProperty('--lift', '0px');
    }

    card.addEventListener('pointerenter', move, { passive: true });
    card.addEventListener('pointermove', move, { passive: true });
    card.addEventListener('pointerleave', reset, { passive: true });
    card.addEventListener('pointercancel', reset, { passive: true });
    card.addEventListener('pointerup', function () {
      if (window.matchMedia && window.matchMedia('(hover: none)').matches) reset();
    }, { passive: true });
  }

  function markTabEntering() {
    window.setTimeout(function () {
      var screen = activeScreen();
      if (!screen) return;
      document.querySelectorAll('.screen.m3-tab-entering').forEach(function (item) {
        if (item !== screen) item.classList.remove('m3-tab-entering');
      });
      screen.classList.add('m3-tab-entering');
      replayCharts(screen);
      window.setTimeout(function () {
        screen.classList.remove('m3-tab-entering');
      }, 1250);
    }, 0);
  }

  function bindNavigation() {
    document.querySelectorAll('.nav-btn').forEach(function (button) {
      if (button.dataset.m3PremiumNavReady) return;
      button.dataset.m3PremiumNavReady = 'true';
      button.addEventListener('click', markTabEntering);
    });
  }

  function numericAttribute(element, name) {
    var value = parseFloat(element.getAttribute(name));
    return Number.isFinite(value) ? value : 0;
  }

  function decorateChart(wrapper) {
    if (!wrapper || wrapper.dataset.m3PremiumChartReady) return;
    var svg = wrapper.querySelector('svg');
    if (!svg) return;

    wrapper.dataset.m3PremiumChartReady = 'true';
    wrapper.classList.add('m3-chart-premium');

    function classify() {
      svg.querySelectorAll('path, polyline').forEach(function (shape) {
        try {
          var stroke = window.getComputedStyle(shape).stroke;
          var length = typeof shape.getTotalLength === 'function' ? shape.getTotalLength() : 0;
          if (stroke && stroke !== 'none' && length > 28) shape.classList.add('m3-data-line');
        } catch (error) { /* malformed SVG paths are ignored */ }
      });

      svg.querySelectorAll('circle').forEach(function (circle) {
        var radius = numericAttribute(circle, 'r');
        if (radius > 0 && radius <= 14) circle.classList.add('m3-data-point');
      });

      svg.querySelectorAll('rect').forEach(function (rect) {
        var width = numericAttribute(rect, 'width');
        var height = numericAttribute(rect, 'height');
        if (width > 2 && height > 4 && width < 110) rect.classList.add('m3-data-bar');
      });
    }

    classify();

    var updateTimer = 0;
    new MutationObserver(function () {
      window.clearTimeout(updateTimer);
      updateTimer = window.setTimeout(function () {
        classify();
        restart(wrapper, 'm3-chart-updating', 760);
      }, 34);
    }).observe(svg, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['d', 'points', 'cx', 'cy', 'r', 'x', 'y', 'width', 'height']
    });
  }

  function replayCharts(scope) {
    if (!scope || reduceMotion) return;
    scope.querySelectorAll('.m3-chart-premium').forEach(function (chart, index) {
      window.setTimeout(function () {
        restart(chart, 'm3-chart-updating', 760);
      }, 120 + index * 85);
    });
  }

  function addContextRing(card) {
    if (!card || reduceMotion || !card.classList.contains('m3-premium-card')) return;
    var existing = card.querySelector('.m3-context-ring');
    if (existing) existing.remove();
    var ring = document.createElement('span');
    ring.className = 'm3-context-ring';
    ring.setAttribute('aria-hidden', 'true');
    card.appendChild(ring);
    ring.addEventListener('animationend', function () { ring.remove(); }, { once: true });
  }

  function animateValue(value) {
    var card = value.closest('.m3-premium-card, .stat, .day-row, .card, .hist-item');
    restart(value, 'm3-context-number', 740);
    if (card) {
      restart(card, 'm3-context-update', 760);
      addContextRing(card);
    }
  }

  function bindContextValue(value) {
    if (!value || value.dataset.m3ContextReady) return;
    value.dataset.m3ContextReady = 'true';
    var previous = value.textContent.trim();

    new MutationObserver(function () {
      var next = value.textContent.trim();
      if (next === previous) return;
      previous = next;
      animateValue(value);
    }).observe(value, { childList: true, characterData: true, subtree: true });
  }

  function decorateHistory(item, index) {
    if (!item || item.dataset.m3HistoryReady) return;
    item.dataset.m3HistoryReady = 'true';
    item.classList.add('m3-history-personality');
    item.style.setProperty('--history-index', String(index % 8));
  }

  function directText(element) {
    return Array.prototype.map.call(element.childNodes, function (node) {
      return node.nodeType === Node.TEXT_NODE ? node.textContent : '';
    }).join(' ').trim();
  }

  function decorateEmptyState(element) {
    if (!element || element.dataset.m3EmptyReady) return;
    var text = (directText(element) || element.textContent || '').replace(/\s+/g, ' ').trim();
    if (!text || text.length > 190) return;
    if (!/(no\s+(history|entries|data|records|tests|weeks|items)|nothing\s+(yet|here)|log\s+your\s+first|start\s+by|no\s+.*\s+yet)/i.test(text)) return;
    if (element.closest('.stat, .m3-hero-card, button, label')) return;

    element.dataset.m3EmptyReady = 'true';
    element.classList.add('m3-empty-state');
    var visual = document.createElement('div');
    visual.className = 'm3-empty-visual';
    visual.setAttribute('aria-hidden', 'true');
    visual.innerHTML = '<span class="m3-empty-orbit"></span><span class="m3-empty-core"></span>';
    element.insertBefore(visual, element.firstChild);
  }

  function bindPointerLight(control) {
    if (!control || control.dataset.m3PointerReady) return;
    control.dataset.m3PointerReady = 'true';

    control.addEventListener('pointermove', function (event) {
      var rect = control.getBoundingClientRect();
      control.style.setProperty('--mx', (event.clientX - rect.left) + 'px');
      control.style.setProperty('--my', (event.clientY - rect.top) + 'px');
      control.classList.add('m3-pointer-active');
    }, { passive: true });
    control.addEventListener('pointerleave', function () {
      control.classList.remove('m3-pointer-active');
    }, { passive: true });
    control.addEventListener('pointerup', function () {
      window.setTimeout(function () { control.classList.remove('m3-pointer-active'); }, 140);
    }, { passive: true });
  }

  function decorate() {
    document.querySelectorAll('.m3-hero-card').forEach(bindPremiumCard);
    document.querySelectorAll('.chart-wrap').forEach(decorateChart);
    document.querySelectorAll('.stat .v, .day-row .dscore, .hist-item .score, [data-score]').forEach(bindContextValue);
    document.querySelectorAll('.hist-item').forEach(decorateHistory);
    document.querySelectorAll('.empty, .empty-state, [class*="empty"], [id*="empty"], .hist-inner > p, .card > p').forEach(decorateEmptyState);
    document.querySelectorAll('.btn, .icon-btn, .gear, .m3-theme-toggle, .weeknav .wbtn').forEach(bindPointerLight);
    bindNavigation();
  }

  function scheduleDecorate() {
    if (decorateFrame) return;
    decorateFrame = window.requestAnimationFrame(function () {
      decorateFrame = 0;
      decorate();
    });
  }

  function initialise() {
    decorate();
    markTabEntering();

    new MutationObserver(function (mutations) {
      var needsDecoration = false;
      mutations.forEach(function (mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length) needsDecoration = true;
        if (mutation.type === 'attributes' &&
            mutation.target.classList &&
            mutation.target.classList.contains('screen') &&
            mutation.target.classList.contains('active')) {
          markTabEntering();
        }
      });
      if (needsDecoration) scheduleDecorate();
    }).observe(document.body, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['class']
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialise, { once: true });
  } else {
    initialise();
  }
})();
