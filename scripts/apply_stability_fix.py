#!/usr/bin/env python3
"""Fix premium animation feedback loops in the standalone ENGRAM bundle."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "app/src/main/assets/engram.html"
CSS_PATH = ROOT / "scripts/stability_fix.css"
MARKER = "engram-premium-stability-v4"


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
        raise RuntimeError(f"Expected one {label} block, found {count}")
    return source.replace(old, new, 1)


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    if html.count(MARKER) >= 2:
        print("Stability fix is already embedded.")
        return

    css_match, css = read_assignment(html, "materialStyle")
    script_match, script = read_assignment(html, "materialScript")

    css_patch = CSS_PATH.read_text(encoding="utf-8").strip()
    css = css.rstrip() + "\n\n" + css_patch + "\n"

    script = replace_once(
        script,
        "  var decorateFrame = 0;\n",
        "  var decorateFrame = 0;\n  var lastActiveScreen = null;\n  var tabEnterTimer = 0;\n",
        "premium state declaration",
    )

    old_tab = """  function markTabEntering() {
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
"""
    new_tab = """  function markTabEntering(force) {
    window.setTimeout(function () {
      var screen = activeScreen();
      if (!screen) return;
      if (!force && screen === lastActiveScreen) return;
      lastActiveScreen = screen;

      document.querySelectorAll('.screen.m3-tab-entering').forEach(function (item) {
        item.classList.remove('m3-tab-entering');
      });
      void screen.offsetWidth;
      screen.classList.add('m3-tab-entering');
      replayCharts(screen);

      window.clearTimeout(tabEnterTimer);
      tabEnterTimer = window.setTimeout(function () {
        screen.classList.remove('m3-tab-entering');
      }, 1250);
    }, 0);
  }
"""
    script = replace_once(script, old_tab, new_tab, "tab-entry function")

    script = replace_once(
        script,
        "      button.addEventListener('click', markTabEntering);\n",
        "      button.addEventListener('click', function () { markTabEntering(true); });\n",
        "navigation replay binding",
    )

    old_chart_observer = """    var updateTimer = 0;
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
"""
    new_chart_observer = """    var updateTimer = 0;
    new MutationObserver(function () {
      window.clearTimeout(updateTimer);
      updateTimer = window.setTimeout(function () {
        classify();
      }, 90);
    }).observe(svg, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['d', 'points', 'cx', 'cy', 'r', 'x', 'y', 'width', 'height']
    });
"""
    script = replace_once(script, old_chart_observer, new_chart_observer, "chart observer")

    old_global_observer = """    new MutationObserver(function (mutations) {
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
"""
    new_global_observer = """    new MutationObserver(function (mutations) {
      var needsDecoration = false;
      mutations.forEach(function (mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length) needsDecoration = true;
        if (mutation.type === 'attributes' &&
            mutation.target.classList &&
            mutation.target.classList.contains('screen')) {
          var oldClasses = ' ' + (mutation.oldValue || '') + ' ';
          var wasActive = oldClasses.indexOf(' active ') !== -1;
          var isActive = mutation.target.classList.contains('active');
          if (!wasActive && isActive) markTabEntering(false);
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
"""
    script = replace_once(script, old_global_observer, new_global_observer, "global observer")

    script = replace_once(
        script,
        "    markTabEntering();\n",
        "    markTabEntering(true);\n",
        "initial tab entry",
    )

    html = replace_assignment(html, script_match, script)
    css_match, _ = read_assignment(html, "materialStyle")
    html = replace_assignment(html, css_match, css)
    HTML_PATH.write_text(html, encoding="utf-8")

    generated = HTML_PATH.read_text(encoding="utf-8")
    required = [
        MARKER,
        "attributeOldValue: true",
        "screen === lastActiveScreen",
        "m3ContextNumberStable",
        "visibility:visible!important",
    ]
    missing = [token for token in required if token not in generated]
    if missing:
        raise RuntimeError(f"Generated bundle is missing required fixes: {missing}")

    print(f"Applied animation stability fix to {HTML_PATH}")
    print(f"Standalone size: {HTML_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
