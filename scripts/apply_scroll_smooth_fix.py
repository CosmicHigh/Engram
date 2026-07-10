#!/usr/bin/env python3
"""Make ENGRAM's scroll reveals early, lightweight and one-shot."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "app/src/main/assets/engram.html"
CSS_PATH = ROOT / "scripts/scroll_smooth_fix.css"
MARKER = "engram-scroll-smooth-v5"


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</script", "<\\/script")


def read_assignment(html: str, variable: str) -> tuple[re.Match[str], str]:
    pattern = re.compile(
        rf"({re.escape(variable)}\.textContent\s*=\s*)"
        r"(\"(?:\\.|[^\"\\])*\")"
        r"(\s*;)"
    )
    match = pattern.search(html)
    if not match:
        raise RuntimeError(f"Could not locate {variable}.textContent")
    return match, json.loads(match.group(2))


def replace_assignment(html: str, match: re.Match[str], value: str) -> str:
    replacement = match.group(1) + js_string(value) + match.group(3)
    return html[:match.start()] + replacement + html[match.end():]


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one {label}, found {count}")
    return source.replace(old, new, 1)


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    if html.count(MARKER) >= 2:
        print("Scroll smoothing fix is already embedded.")
        return

    css_match, css = read_assignment(html, "materialStyle")
    script_match, script = read_assignment(html, "materialScript")

    css_patch = CSS_PATH.read_text(encoding="utf-8").strip()
    css = css.rstrip() + "\n\n" + css_patch + "\n"

    old_reveal = """  var revealObserver = !reduceMotion && 'IntersectionObserver' in window
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
"""

    new_reveal = """  function settleReveal(element) {
    if (!element || element.classList.contains('m3-reveal-settled')) return;
    element.classList.remove('m3-reveal', 'm3-visible');
    element.classList.add('m3-reveal-settled');
  }

  function showReveal(element) {
    if (!element || element.classList.contains('m3-reveal-settled') ||
        element.classList.contains('m3-visible')) return;
    element.classList.add('m3-visible');
    if (revealObserver) revealObserver.unobserve(element);
    window.setTimeout(function () { settleReveal(element); }, 430);
  }

  var revealObserver = !reduceMotion && 'IntersectionObserver' in window
    ? new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          showReveal(entry.target);
        });
      }, { threshold: 0, rootMargin: '120px 0px 220px 0px' })
    : null;

  function registerReveal(element) {
    if (!element || element.nodeType !== 1 || element.dataset.m3RevealReady) return;
    element.dataset.m3RevealReady = 'true';
    if (!revealObserver) {
      element.classList.add('m3-reveal-settled');
      return;
    }
    element.classList.add('m3-reveal');
    revealObserver.observe(element);
  }

  function revealInActiveScreen() {
    window.requestAnimationFrame(function () {
      var active = document.querySelector('.screen.active');
      if (!active) return;
      var nearby = [];
      active.querySelectorAll('.m3-reveal').forEach(function (element) {
        var rect = element.getBoundingClientRect();
        if (rect.top < window.innerHeight + 220 && rect.bottom > -120) nearby.push(element);
      });
      nearby.forEach(function (element, index) {
        window.setTimeout(function () { showReveal(element); }, Math.min(index * 22, 110));
      });
    });
  }
"""

    script = replace_once(script, old_reveal, new_reveal, "reveal system")

    scroll_guard = """

/* engram-scroll-smooth-v5 */
(function () {
  'use strict';
  if (window.__engramScrollSmoothV5) return;
  window.__engramScrollSmoothV5 = true;

  var root = document.documentElement;
  var idleTimer = 0;

  function markScrolling() {
    root.classList.add('m3-user-scrolling');
    window.clearTimeout(idleTimer);
    idleTimer = window.setTimeout(function () {
      root.classList.remove('m3-user-scrolling');
    }, 120);
  }

  window.addEventListener('scroll', markScrolling, { passive: true });
  window.addEventListener('touchmove', markScrolling, { passive: true });
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) root.classList.remove('m3-user-scrolling');
  });
})();
"""
    script = script.rstrip() + scroll_guard

    html = replace_assignment(html, script_match, script)
    css_match, _ = read_assignment(html, "materialStyle")
    html = replace_assignment(html, css_match, css)
    HTML_PATH.write_text(html, encoding="utf-8")

    generated = HTML_PATH.read_text(encoding="utf-8")
    required = [
        MARKER,
        "rootMargin: '120px 0px 220px 0px'",
        "threshold: 0",
        "m3-reveal-settled",
        "m3-user-scrolling",
        "translate3d(0,12px,0)",
    ]
    missing = [token for token in required if token not in generated]
    if missing:
        raise RuntimeError(f"Generated bundle is missing scroll fixes: {missing}")

    print(f"Applied smooth scroll reveals to {HTML_PATH}")
    print(f"Standalone size: {HTML_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
