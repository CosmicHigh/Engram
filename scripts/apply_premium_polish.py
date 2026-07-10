#!/usr/bin/env python3
"""Inline the premium polish CSS/JS into the standalone ENGRAM bundle."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "app/src/main/assets/engram.html"
CSS_PATH = ROOT / "scripts/premium_polish.css"
JS_PATH = ROOT / "scripts/premium_polish.js"
MARKER = "engram-premium-polish-v3"


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</script", "<\\/script")


def append_to_assignment(html: str, variable: str, patch: str) -> tuple[str, str]:
    pattern = re.compile(
        rf"({re.escape(variable)}\.textContent\s*=\s*)"
        r"(\"(?:\\.|[^\"\\])*\")"
        r"(\s*;)"
    )
    match = pattern.search(html)
    if not match:
        raise RuntimeError(f"Could not locate {variable}.textContent")

    current = json.loads(match.group(2))
    if MARKER in current:
        return html, current

    combined = current.rstrip() + "\n\n" + patch.strip() + "\n"
    replacement = match.group(1) + js_string(combined) + match.group(3)
    return html[:match.start()] + replacement + html[match.end():], combined


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    if html.count(MARKER) >= 2:
        print("Premium polish is already embedded.")
        return

    css_patch = CSS_PATH.read_text(encoding="utf-8")
    js_patch = JS_PATH.read_text(encoding="utf-8")

    html, css = append_to_assignment(html, "materialStyle", css_patch)
    html, js = append_to_assignment(html, "materialScript", js_patch)
    HTML_PATH.write_text(html, encoding="utf-8")

    required_css = [
        ".m3-premium-card",
        ".m3-chart-premium",
        ".m3-empty-state",
        ".m3-history-personality",
        "@keyframes m3ContextNumber",
    ]
    required_js = [
        "__engramPremiumPolishV3",
        "decorateChart",
        "bindContextValue",
        "decorateEmptyState",
        "bindPremiumCard",
    ]
    missing = [token for token in required_css if token not in css]
    missing += [token for token in required_js if token not in js]
    if missing:
        raise RuntimeError(f"Generated bundle is missing: {missing}")

    print(f"Embedded premium polish into {HTML_PATH}")
    print(f"Standalone size: {HTML_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
