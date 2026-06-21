#!/usr/bin/env python3
"""Append flagged URLs to state/seen_urls.json — called by the flag-pick workflow.

Usage: python flag_ledger.py <path-to-seen_urls.json> '<json-array-of-urls>'
Exit 0 always (even if nothing new, so the workflow commit step handles it cleanly).
"""
import json, sys, datetime, os


def main():
    if len(sys.argv) < 3:
        print("Usage: flag_ledger.py <seen_urls.json> '<json-array>'")
        sys.exit(1)

    path = sys.argv[1]
    try:
        new_urls = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(new_urls, str):
        new_urls = [new_urls]
    if not isinstance(new_urls, list):
        print(f"Expected a JSON array, got: {type(new_urls)}", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(path):
        data = json.load(open(path, encoding="utf-8"))
    else:
        data = {"urls": []}

    existing = set(data.get("urls", []))
    added = [u for u in new_urls if u and u not in existing]

    if not added:
        print("No new URLs — all already in ledger")
        return

    data["urls"] = data.get("urls", []) + added
    data["updated"] = datetime.date.today().isoformat()
    data["count"] = len(data["urls"])
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Added {len(added)} URL(s): {added}")


if __name__ == "__main__":
    main()
