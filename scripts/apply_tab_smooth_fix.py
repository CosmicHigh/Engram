#!/usr/bin/env python3
"""Remove premium tab replay work while keeping the standalone visual polish."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "app/src/main/assets/engram.html"
CSS_PATH = ROOT / "scripts/tab_smooth_fix.css"
MARKER = "engram-tab-smooth-v6"


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
        print("Tab smoothing fix is already embedded.")
        return

    css_match, css = read_assignment(html, "materialStyle")
    script_match, script = read_assignment(html, "materialScript")

    css = css.rstrip() + "\n\n" + CSS_PATH.read_text(encoding="utf-8").strip() + "\n"

    old_mark = """  function markTabEntering(force) {
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
    new_mark = """  function markTabEntering() {
    var screen = activeScreen();
    lastActiveScreen = screen;
    window.clearTimeout(tabEnterTimer);
    document.querySelectorAll('.screen.m3-tab-entering').forEach(function (item) {
      item.classList.remove('m3-tab-entering');
    });
  }
"""
    script = replace_once(script, old_mark, new_mark, "premium tab-entry function")

    old_replay = """  function replayCharts(scope) {
    if (!scope || reduceMotion) return;
    scope.querySelectorAll('.m3-chart-premium').forEach(function (chart, index) {
      window.setTimeout(function () {
        restart(chart, 'm3-chart-updating', 760);
      }, 120 + index * 85);
    });
  }
"""
    new_replay = """  function replayCharts() {
    /* Intentionally disabled: chart replays during tab switches caused frame drops on mobile. */
  }
"""
    script = replace_once(script, old_replay, new_replay, "chart replay function")

    script = script.replace(
        "      button.addEventListener('click', function () { markTabEntering(true); });\n",
        "      button.addEventListener('click', markTabEntering);\n",
        1,
    )
    script = script.replace("    markTabEntering(true);\n", "    markTabEntering();\n", 1)
    script = script.replace("if (!wasActive && isActive) markTabEntering(false);", "if (!wasActive && isActive) markTabEntering();", 1)

    html = replace_assignment(html, script_match, script)
    css_match, _ = read_assignment(html, "materialStyle")
    html = replace_assignment(html, css_match, css)
    HTML_PATH.write_text(html, encoding="utf-8")

    generated = HTML_PATH.read_text(encoding="utf-8")
    required = [
        MARKER,
        "function replayCharts()",
        "chart replays during tab switches caused frame drops",
        "@media(hover:none)",
        "m3-premium-grid",
    ]
    missing = [token for token in required if token not in generated]
    if missing:
        raise RuntimeError(f"Generated bundle is missing tab fixes: {missing}")

    forbidden = [
        "screen.classList.add('m3-tab-entering')",
        "replayCharts(screen)",
    ]
    present = [token for token in forbidden if token in generated]
    if present:
        raise RuntimeError(f"Premium tab replay code remains: {present}")

    print(f"Applied smooth tab switching to {HTML_PATH}")
    print(f"Standalone size: {HTML_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
