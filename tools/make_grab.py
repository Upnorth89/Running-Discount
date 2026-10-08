#!/usr/bin/env python3
"""Rebuild the "Grab deals" bookmark in site/grab.html from site/grab.js (Oct 9, 2026: phone version).

The drag-to-bar button (computers) and the "Copy the bookmark" box (phones) both carry grab.js as a javascript: link.
Run after any change to grab.js:   python tools/make_grab.py
"""
import re
from pathlib import Path
from urllib.parse import quote

SITE = Path(__file__).resolve().parents[1] / "site"
js = (SITE / "grab.js").read_text()
js = re.sub(r"^/\*.*?\*/\s*", "", js, flags=re.S)              # the header comment isn't needed in the bookmark
link = "javascript:" + quote(js, safe=" ()[]{}=>,;:./!?$`'*+-_~|@^")
page = (SITE / "grab.html").read_text()
page = re.sub(r'<a class="bm" href="javascript:[^"]*"', lambda m: f'<a class="bm" href="{link}"', page)
page = re.sub(r'(<textarea id="code"[^>]*>)[^<]*(</textarea>)', lambda m: m.group(1) + link.replace("&", "&amp;") + m.group(2), page)
(SITE / "grab.html").write_text(page)
print(f"grab.html: bookmark rebuilt ({len(link)} characters)")
