/*
 * ENGRAM Material 3 expressive behaviour layer.
 * Presentation only: tracker state, calculations and backup logic remain in engram.html.
 */
(function () {
  'use strict';

  if (window.__engramMaterialReady) return;
  window.__engramMaterialReady = true;

  var root = document.documentElement;
  var THEME_KEY = 'engram-m3-theme';
  var tabs = ['gt', 'inst', 'exec', 'week'];
  var toastTimer = null;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function storageGet(key) {
    try { return localStorage.getItem(key); } catch (error) { return null; }
  }

  function storageSet(key, value) {
    try { localStorage.setItem(key, value); } catch (error) { /* optional */ }
  }

  function systemTheme() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function currentTheme() {
    return root.getAttribute('data-m3-theme') || storageGet(THEME_KEY) || systemTheme();
  }

  function themeIcon(theme) {
    if (theme === 'dark') {
      return '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M20.4 15.5A8.4 8.4 0 0 1 8.5 3.6 8.5 8.5 0 1 0 20.4 15.5Z"></path></svg>';
    }
    return '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"></path></svg>';
  }

  function updateThemeControl() {
    var button = document.querySelector('.m3-theme-toggle');
    if (!button) return;
    var theme = currentTheme();
    button.innerHTML = themeIcon(theme);
    button.setAttribute('aria-label', theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
    button.setAttribute('title', theme === 'dark' ? 'Light theme' : 'Dark theme');
  }

  function updateThemeColor() {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.name = 'theme-color';
      document.head.appendChild(meta);
    }
    meta.content = currentTheme() === 'dark' ? '#141218' : '#fdf8ff';
  }

  function setTheme(theme, announce) {
    var resolved = theme === 'dark' ? 'dark' : 'light';
    root.setAttribute('data-m3-theme', resolved);
    storageSet(THEME_KEY, resolved);
    updateThemeControl();
    updateThemeColor();
    if (announce) showToast(resolved === 'dark' ? 'Dark theme on' : 'Light theme on');
  }

  function activeTab() {
    var active = document.querySelector('.nav-btn.active');
    if (active && active.id && active.id.indexOf('nav-') === 0) return active.id.slice(4);
    var screen = document.querySelector('.screen.active');
    if (screen && screen.id && screen.id.indexOf('s-') === 0) return screen.id.slice(2);
    return 'gt';
  }

  function setTab(tab) {
    if (tabs.indexOf(tab) === -1) tab = 'gt';
    root.setAttribute('data-m3-tab', tab);
  }

  function showToast(message) {
    var toast = document.querySelector('.m3-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'm3-toast';
      toast.setAttribute('role', 'status');
      toast.setAttribute('aria-live', 'polite');
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    window.clearTimeout(toastTimer);
    requestAnimationFrame(function () { toast.classList.add('show'); });
    toastTimer = window.setTimeout(function () { toast.classList.remove('show'); }, 1500);
  }

  function softHaptic(duration) {
    try {
      if (navigator.vibrate) navigator.vibrate(duration || 7);
    } catch (error) { /* optional */ }
  }

  function installTopActions() {
    var topbar = document.querySelector('.topbar');
    var gear = topbar && topbar.querySelector('.gear');
    if (!topbar || !gear || topbar.querySelector('.m3-top-actions')) return;

    var actions = document.createElement('div');
    actions.className = 'm3-top-actions';

    var themeButton = document.createElement('button');
    themeButton.type = 'button';
    themeButton.className = 'm3-theme-toggle';
    themeButton.addEventListener('click', function () {
      setTheme(currentTheme() === 'dark' ? 'light' : 'dark', true);
      softHaptic(10);
    });

    topbar.insertBefore(actions, gear);
    actions.appendChild(themeButton);
    actions.appendChild(gear);
    updateThemeControl();
  }

  function addRipple(event) {
    var target = event.target.closest('button, .hist-head, .day-row');
    if (!target || target.disabled || reduceMotion) return;

    var rect = target.getBoundingClientRect();
    var ripple = document.createElement('span');
    ripple.className = 'm3-ripple';
    ripple.style.left = (event.clientX - rect.left) + 'px';
    ripple.style.top = (event.clientY - rect.top) + 'px';

    var computed = window.getComputedStyle(target);
    if (computed.position === 'static') target.style.position = 'relative';
    if (computed.overflow === 'visible') target.style.overflow = 'hidden';

    target.appendChild(ripple);
    ripple.addEventListener('animationend', function () { ripple.remove(); }, { once: true });
  }

  function animateNav(button) {
    if (!button) return;
    button.classList.remove('m3-bounce');
    void button.offsetWidth;
    button.classList.add('m3-bounce');
    window.setTimeout(function () { button.classList.remove('m3-bounce'); }, 560);
  }

  var revealObserver = !reduceMotion && 'IntersectionObserver' in window
    ? new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('m3-visible');
          revealObserver.unobserve(entry.target);
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -24px 0px' })
    : null;

  function registerReveal(element) {
    if (!element || element.nodeType !== 1 || element.dataset.m3RevealReady) return;
    element.dataset.m3RevealReady = 'true';
    if (!revealObserver) {
      element.classList.add('m3-visible');
      return;
    }
    element.classList.add('m3-reveal');
    revealObserver.observe(element);
  }

  function revealInActiveScreen() {
    window.setTimeout(function () {
      var active = document.querySelector('.screen.active');
      if (!active) return;
      active.querySelectorAll('.m3-reveal').forEach(function (element, index) {
        window.setTimeout(function () { element.classList.add('m3-visible'); }, Math.min(index * 28, 220));
      });
    }, 40);
  }

  function watchNumber(element) {
    if (!element || element.dataset.m3NumberReady) return;
    element.dataset.m3NumberReady = 'true';
    new MutationObserver(function () {
      if (reduceMotion) return;
      element.classList.remove('m3-pop');
      void element.offsetWidth;
      element.classList.add('m3-pop');
    }).observe(element, { childList: true, characterData: true, subtree: true });
  }

  function decorate(scope) {
    var node = scope && scope.nodeType === 1 ? scope : document;
    var revealSelector = '.card, .stat, .hist-item, .verdict';
    if (node.matches && node.matches(revealSelector)) registerReveal(node);
    if (node.querySelectorAll) node.querySelectorAll(revealSelector).forEach(registerReveal);
    if (node.matches && node.matches('.stat .v')) watchNumber(node);
    if (node.querySelectorAll) node.querySelectorAll('.stat .v').forEach(watchNumber);
  }

  function bindNavigation() {
    document.querySelectorAll('.nav-btn').forEach(function (button) {
      if (button.dataset.m3NavReady) return;
      button.dataset.m3NavReady = 'true';
      button.addEventListener('click', function () {
        var tab = button.id && button.id.indexOf('nav-') === 0 ? button.id.slice(4) : activeTab();
        setTab(tab);
        animateNav(button);
        revealInActiveScreen();
        softHaptic(7);
      });
    });
  }

  function initialise() {
    setTheme(storageGet(THEME_KEY) || systemTheme(), false);
    setTab(activeTab());
    installTopActions();
    bindNavigation();
    decorate(document);
    revealInActiveScreen();

    document.addEventListener('pointerdown', addRipple, { passive: true });
    document.addEventListener('click', function (event) {
      var button = event.target.closest('.btn-primary, .icon-btn, .weeknav .wbtn');
      if (button) softHaptic(6);
    }, { passive: true });

    new MutationObserver(function (mutations) {
      var refreshTab = false;
      mutations.forEach(function (mutation) {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach(function (added) {
            if (added.nodeType === 1) decorate(added);
          });
        }
        if (mutation.type === 'attributes' &&
            (mutation.target.classList.contains('nav-btn') || mutation.target.classList.contains('screen'))) {
          refreshTab = true;
        }
      });
      bindNavigation();
      if (refreshTab) {
        setTab(activeTab());
        revealInActiveScreen();
      }
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
