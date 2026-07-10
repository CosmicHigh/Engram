#!/usr/bin/env python3
"""Inline the Material presentation layer into ENGRAM's self-unpacking HTML.

The generated app/src/main/assets/engram.html has no runtime dependency on
material_you.css or material_you.js and works when downloaded by itself.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "app/src/main/assets/engram.html"
CSS_PATH = ROOT / "app/src/main/assets/material_you.css"
JS_PATH = ROOT / "app/src/main/assets/material_you.js"
MARKER = "engram-material-inline-v1"


def javascript_string(value: str) -> str:
    # JSON is a valid JavaScript string literal. Guard against a future source
    # containing a literal closing script tag inside the outer loader script.
    return json.dumps(value, ensure_ascii=False).replace("</script", "<\\/script")


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    if MARKER in html:
        print("Material layer is already inlined; no change required.")
        return

    css = CSS_PATH.read_text(encoding="utf-8")
    js = JS_PATH.read_text(encoding="utf-8")

    needle = (
        "    const doc = new DOMParser().parseFromString(template, 'text/html');\n"
        "    document.documentElement.replaceWith(doc.documentElement);"
    )
    if html.count(needle) != 1:
        raise RuntimeError("Could not locate the unique bundle DOM replacement hook")

    replacement = (
        "    const doc = new DOMParser().parseFromString(template, 'text/html');\n"
        f"    // {MARKER}: standalone Material 3 presentation layer.\n"
        "    const materialStyle = doc.createElement('style');\n"
        "    materialStyle.id = 'engram-material-css';\n"
        f"    materialStyle.textContent = {javascript_string(css)};\n"
        "    doc.head.appendChild(materialStyle);\n"
        "    const materialScript = doc.createElement('script');\n"
        "    materialScript.id = 'engram-material-js';\n"
        f"    materialScript.textContent = {javascript_string(js)};\n"
        "    doc.body.appendChild(materialScript);\n"
        "    document.documentElement.replaceWith(doc.documentElement);"
    )

    HTML_PATH.write_text(html.replace(needle, replacement), encoding="utf-8")

    generated = HTML_PATH.read_text(encoding="utf-8")
    required = [MARKER, "engram-material-css", "engram-material-js", "data-m3-theme"]
    missing = [token for token in required if token not in generated]
    if missing:
        raise RuntimeError(f"Generated HTML is missing required tokens: {missing}")

    print(f"Inlined Material CSS and JavaScript into {HTML_PATH}")
    print(f"Generated size: {HTML_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
