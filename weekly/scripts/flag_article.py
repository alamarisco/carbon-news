#!/usr/bin/env python3
"""Append a flagged article to the current week's queue (FLAG mode).

Usage:
    python flag_article.py --root "<...01_每周國際新聞資訊蒐集>" --week 2026.06.15-06.18 \
        --url URL [--source S] [--date YYYY/MM/DD] [--by NAME] [--headline H] [--note N]

Creates the queue file from the template if it doesn't exist. Skips silently if the
URL is already queued.
"""
import argparse, os, re, datetime

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--week", required=True, help="week_label, e.g. 2026.06.15-06.18")
ap.add_argument("--url", required=True)
ap.add_argument("--source", default="")
ap.add_argument("--date", default="")
ap.add_argument("--by", default="")
ap.add_argument("--headline", default="")
ap.add_argument("--note", default="")
a = ap.parse_args()

year = a.week[:4]
qdir = os.path.join(a.root, f"{year}年")
os.makedirs(qdir, exist_ok=True)
qpath = os.path.join(qdir, f"_queue_{a.week}.md")

if os.path.exists(qpath):
    existing = open(qpath, encoding="utf-8").read()
else:
    existing = f"# 本週候選新聞佇列 (CBAM Weekly Queue) — {a.week}\n\n"

if a.url in existing:
    print("Already queued — skipped:", a.url)
    raise SystemExit(0)

block = (
    "---\n"
    f"- url: {a.url}\n"
    f"  source: {a.source}\n"
    f"  date: {a.date}\n"
    f"  flagged_by: {a.by}\n"
    f"  headline: {a.headline}\n"
    f"  note: {a.note}\n"
)
with open(qpath, "a", encoding="utf-8") as f:
    if not existing.endswith("\n"):
        f.write("\n")
    f.write(block)
print("Flagged to", qpath)
