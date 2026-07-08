#!/usr/bin/env python3
"""Parse a RADAR digest email into a numbered, machine-readable item list.

Used by the carbon-news-collector skill's RADAR mode: fetch the daily/weekly digest email's
HTML body (via the Gmail connector — the raw/full body, not a quoted or re-rendered copy),
save it to a file, then run this against it.

    python parse_digest_email.py --html /tmp/digest.html --out /tmp/digest.json

Extracts the hidden <!--RADAR_ITEMS_JSON:[...]--> payload that render_email.py embeds — this
is robust to Gmail reformatting/quoting since it's a plain substring match, not HTML parsing.
Writes JSON to --out and prints a numbered plain-text list to stdout for pasting into chat.

Exit codes: 0 = parsed; 2 = no marker found (wrong email / body wasn't the raw HTML).
"""
import argparse, json, re, sys

MARKER_RE = re.compile(r"<!--RADAR_ITEMS_JSON:(.*?)-->", re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True, help="path to the saved email HTML body")
    ap.add_argument("--out", required=True, help="path to write parsed items JSON")
    a = ap.parse_args()

    text = open(a.html, encoding="utf-8", errors="ignore").read()
    m = MARKER_RE.search(text)
    if not m:
        print("[parse] No RADAR_ITEMS_JSON marker found — make sure you fetched the raw HTML "
              "body of the digest email (not a plain-text/quoted copy).", file=sys.stderr)
        sys.exit(2)

    items = json.loads(m.group(1))
    json.dump({"items": items}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    for i in items:
        label = i.get("tier") or i.get("topic") or ""
        print(f"{i['n']}. [{label}] {i['title']}")
        print(f"   {i.get('source','')} · {i.get('published','')}" +
              (f" · {i['topic']}" if i.get("tier") else ""))
        print(f"   {i['url']}")
        print()

    print(f"[parse] {len(items)} item(s) → {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
