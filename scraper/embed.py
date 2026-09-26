#!/usr/bin/env python3
"""Build a self-contained copy of the page with deals.json baked in
(for the claude.ai artifact, which can't fetch files from other hosts).
Usage: python scraper/embed.py [site/deals.json] [dist/artifact.html]"""
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
deals = Path(sys.argv[1] if len(sys.argv) > 1 else root / "site" / "deals.json").read_text()
out = Path(sys.argv[2] if len(sys.argv) > 2 else root / "dist" / "artifact.html")
page = (root / "site" / "index.html").read_text()
marker = "let DATA=null;"
assert marker in page, "site/index.html must contain 'let DATA=null;'"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(page.replace(marker, "let DATA=" + deals.replace("</", "<\\/") + ";", 1))
print(f"wrote {out}")
