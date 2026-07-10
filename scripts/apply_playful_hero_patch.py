#!/usr/bin/env python3
"""Append the playful hero CSS/JS to ENGRAM's existing standalone bundle."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "app/src/main/assets/engram.html"
CSS_PATCH = ROOT / "scripts/material_playful_patch.css"
JS_PATCH = ROOT / "scripts/material_playful_patch.js"
MARKER = "engram-playful-hero-v2"


def encode_js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</script", "<\\/script")


def append_assignment(html: str, variable: str, patch: str) -> tuple[str, str]:
    pattern = re.compile(
        rf"({re.escape(variable)}\.textContent\s*=\s*)"
        r"(\"(?:\\.|[^\"\\])*\")"
        r"(\s*;)"
    )
    match = pattern.search(html)
    if not match:
        raise RuntimeError(f"Could not find {variable}.textContent assignment")

    existing = json.loads(match.group(2))
    if MARKER in existing:
        return html, existing

    combined = existing.rstrip() + "\n\n" + patch.strip() + "\n"
    replacement = match.group(1) + encode_js_string(combined) + match.group(3)
    return html[:match.start()] + replacement + html[match.end():], combined


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    if html.count(MARKER) >= 2:
        print("Playful hero patch is already embedded; no change required.")
        return

    css_patch = CSS_PATCH.read_text(encoding="utf-8")
    js_patch = JS_PATCH.read_text(encoding="utf-8")

    html, css = append_assignment(html, "materialStyle", css_patch)
    html, js = append_assignment(html, "materialScript", js_patch)
    HTML_PATH.write_text(html, encoding="utf-8")

    required_css = [
        ".m3-hero-card",
        "@keyframes m3HeroLand",
        "@keyframes m3SparkFly",
        "prefers-reduced-motion",
    ]
    required_js = [
        "__engramPlayfulHeroV2",
        "markHeroes",
        "sparkBurst",
        "m3-hero-grid",
    ]
    missing = [token for token in required_css if token not in css]
    missing += [token for token in required_js if token not in js]
    if missing:
        raise RuntimeError(f"Generated bundle is missing required tokens: {missing}")

    print(f"Embedded playful hero patch into {HTML_PATH}")
    print(f"Standalone HTML size: {HTML_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
