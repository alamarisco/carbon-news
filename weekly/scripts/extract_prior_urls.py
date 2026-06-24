#!/usr/bin/env python3
"""Build the dedupe set of URLs already used in prior weekly files.

Usage:
    python extract_prior_urls.py "<path to ...\\01_每周國際新聞資訊蒐集>" [--weeks N]

Prints one URL per line (most recent N weeks, default all) so a story is never repeated.
"""
import sys, glob, re, os, argparse
try:
    import docx
except ImportError:
    sys.exit("pip install python-docx --break-system-packages")

ap = argparse.ArgumentParser()
ap.add_argument("root")
ap.add_argument("--weeks", type=int, default=0, help="limit to most recent N files (0 = all)")
a = ap.parse_args()

files = sorted(glob.glob(os.path.join(a.root, "**", "每週國際新聞蒐集_*.docx"), recursive=True))
files = [f for f in files if "~$" not in f]
if a.weeks:
    files = files[-a.weeks:]

urls = set()
for f in files:
    try:
        d = docx.Document(f)
    except Exception:
        continue
    for p in d.paragraphs:
        m = re.search(r"https?://\S+", p.text)
        if m and ("出處" in p.text or "來源" in p.text or p.text.strip().startswith("http")):
            urls.add(m.group(0).rstrip("。，） )"))

for u in sorted(urls):
    print(u)
