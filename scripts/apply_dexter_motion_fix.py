#!/usr/bin/env python3
"""Replace ENGRAM's orchestration-heavy motion with Dexter's narrow trigger model."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "app/src/main/assets/engram.html"
CSS_PATH = ROOT / "scripts/dexter_motion_fix.css"
MARKER = "engram-dexter-motion-v7"


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


def remove_marked_iife(source: str, marker: str) -> str:
    start = source.find("/* " + marker)
    if start < 0:
        raise RuntimeError(f"Could not find {marker} section")
    end = source.find("\n})();", start)
    if end < 0:
        raise RuntimeError(f"Could not find end of {marker} section")
    end += len("\n})();")
    return source[:start].rstrip() + "\n\n" + source[end:].lstrip()


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    if html.count(MARKER) >= 1:
        print("Dexter-style motion fix is already embedded.")
        return

    css_match, css = read_assignment(html, "materialStyle")
    script_match, script = read_assignment(html, "materialScript")

    css = css.rstrip() + "\n\n" + CSS_PATH.read_text(encoding="utf-8").strip() + "\n"

    old_reveal = """  function settleReveal(element) {
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
    new_reveal = """  function registerReveal(element) {
    if (!element || element.nodeType !== 1 || element.dataset.m3RevealReady) return;
    element.dataset.m3RevealReady = 'true';
    element.classList.remove('m3-reveal', 'm3-visible');
    element.classList.add('m3-reveal-settled');
  }

  function revealInActiveScreen() {
    /* Dexter-style motion: the screen enters as one unit; cards stay rendered. */
  }
"""
    script = replace_once(script, old_reveal, new_reveal, "observer reveal system")

    old_playful_init = """  function initialisePlayfulLayer() {
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
"""
    new_playful_init = """  function initialisePlayfulLayer() {
    markHeroes();
    document.addEventListener('pointerdown', playfulTap, { passive: true });

    new MutationObserver(function (mutations) {
      var shouldMark = mutations.some(function (mutation) {
        return mutation.type === 'childList' && mutation.addedNodes.length;
      });
      if (shouldMark) scheduleMark();
    }).observe(document.body, {
      subtree: true,
      childList: true
    });
  }
"""
    script = replace_once(script, old_playful_init, new_playful_init, "playful observer")

    old_premium_init = """  function initialise() {
    decorate();
    markTabEntering();

    new MutationObserver(function (mutations) {
      var needsDecoration = false;
      mutations.forEach(function (mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length) needsDecoration = true;
        if (mutation.type === 'attributes' &&
            mutation.target.classList &&
            mutation.target.classList.contains('screen')) {
          var oldClasses = ' ' + (mutation.oldValue || '') + ' ';
          var wasActive = oldClasses.indexOf(' active ') !== -1;
          var isActive = mutation.target.classList.contains('active');
          if (!wasActive && isActive) markTabEntering();
        }
      });
      if (needsDecoration) scheduleDecorate();
    }).observe(document.body, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeOldValue: true,
      attributeFilter: ['class']
    });
  }
"""
    new_premium_init = """  function initialise() {
    decorate();

    new MutationObserver(function (mutations) {
      var needsDecoration = mutations.some(function (mutation) {
        return mutation.type === 'childList' && mutation.addedNodes.length;
      });
      if (needsDecoration) scheduleDecorate();
    }).observe(document.body, {
      subtree: true,
      childList: true
    });
  }
"""
    script = replace_once(script, old_premium_init, new_premium_init, "premium observer")

    # This listener existed solely to pause effects that no longer run.
    script = remove_marked_iife(script, "engram-scroll-smooth-v5")

    html = replace_assignment(html, script_match, script)
    css_match, _ = read_assignment(html, "materialStyle")
    html = replace_assignment(html, css_match, css)
    HTML_PATH.write_text(html, encoding="utf-8")

    generated = HTML_PATH.read_text(encoding="utf-8")
    required = [
        MARKER,
        "m3DexterScreenIn",
        "the screen enters as one unit",
        "subtree: true,\n      childList: true",
        "f-dayTotal",
    ]
    missing = [token for token in required if token not in generated]
    if missing:
        raise RuntimeError(f"Generated bundle is missing Dexter motion tokens: {missing}")

    forbidden = [
        "new IntersectionObserver",
        "rootMargin: '120px 0px 220px 0px'",
        "engram-scroll-smooth-v5",
        "screen.classList.add('m3-tab-entering')",
        "replayCharts(screen)",
        "attributeOldValue: true",
    ]
    present = [token for token in forbidden if token in generated]
    if present:
        raise RuntimeError(f"Orchestration-heavy motion remains: {present}")

    print(f"Applied Dexter-style motion architecture to {HTML_PATH}")
    print(f"Standalone size: {HTML_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
