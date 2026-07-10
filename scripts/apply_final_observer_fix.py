#!/usr/bin/env python3
"""Remove the final class observer from ENGRAM's tab-navigation path."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "app/src/main/assets/engram.html"
MARKER = "engram-dexter-observer-v8"


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


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    script_match, script = read_assignment(html, "materialScript")

    if MARKER in script:
        print("Final observer fix is already embedded.")
        return

    old = """    new MutationObserver(function (mutations) {
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
"""

    new = """    /* engram-dexter-observer-v8: tab class changes do not invoke observers. */
    new MutationObserver(function (mutations) {
      var hasAddedNodes = false;
      mutations.forEach(function (mutation) {
        if (mutation.type !== 'childList' || !mutation.addedNodes.length) return;
        hasAddedNodes = true;
        mutation.addedNodes.forEach(function (added) {
          if (added.nodeType === 1) decorate(added);
        });
      });
      if (hasAddedNodes) bindNavigation();
    }).observe(document.body, {
      subtree: true,
      childList: true
    });
"""

    count = script.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one global class observer, found {count}")

    script = script.replace(old, new, 1)
    html = replace_assignment(html, script_match, script)
    HTML_PATH.write_text(html, encoding="utf-8")

    generated = HTML_PATH.read_text(encoding="utf-8")
    required = [
        MARKER,
        "engram-dexter-motion-v7",
        "m3DexterScreenIn",
        "f-dayTotal",
    ]
    forbidden = [
        "attributeFilter: ['class']",
        "refreshTab = false",
        "screen.classList.add('m3-tab-entering')",
        "new IntersectionObserver",
    ]
    missing = [token for token in required if token not in generated]
    present = [token for token in forbidden if token in generated]
    if missing:
        raise RuntimeError(f"Missing required tokens: {missing}")
    if present:
        raise RuntimeError(f"Navigation-triggered motion remains: {present}")

    print(f"Removed final class observer from {HTML_PATH}")
    print(f"Standalone size: {HTML_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
