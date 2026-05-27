#!/usr/bin/env python3
"""
CBAM Monitor — RSS Feed Checker
================================
Verifies which RSS feed URLs actually respond and return entries.
Run this from GitHub Codespace or your local machine (not Cowork sandbox,
which blocks outbound HTTP).

Usage:
  pip install feedparser requests
  python check_feeds.py

The script tries each candidate URL for each source and prints a ✅/❌
summary, then outputs a corrected RSS_FEEDS block you can paste directly
into fetch_feeds.py.
"""

import sys
from datetime import datetime

try:
    import feedparser
    import requests
except ImportError:
    print("Run: pip install feedparser requests")
    sys.exit(1)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
}

# ── Candidate feeds to test ───────────────────────────────────────────────────
# Format: source_name → list of (url, source_type) tuples
# First working URL wins for each source.

CANDIDATES = {

    # ── EU policy / analysis ──────────────────────────────────────────────
    "Euractiv — Climate & Environment": [
        ("https://www.euractiv.com/sections/climate-environment/feed/", "free"),
        ("https://euractiv.com/sections/climate-environment/feed/", "free"),
    ],
    "Euractiv — Trade": [
        ("https://www.euractiv.com/sections/trade/feed/", "free"),
    ],
    "Euractiv — Energy": [
        ("https://www.euractiv.com/sections/energy/feed/", "free"),
    ],
    "Carbon Brief": [
        ("https://feeds.feedburner.com/carbonbrief", "free"),  # confirmed canonical (Feedspot, May 2026)
        ("https://www.carbonbrief.org/feed/", "free"),          # fallback if FeedBurner redirects
    ],
    "Carbon Pulse": [
        ("https://carbon-pulse.com/feed/", "free"),
        ("https://carbon-pulse.com/feed/atom/", "free"),
    ],
    "E3G": [
        ("https://www.e3g.org/feed/", "free"),
        ("https://e3g.org/feed/", "free"),
    ],
    "Sandbag": [
        ("https://sandbag.org.uk/feed/", "free"),
        ("https://www.sandbag.org.uk/feed/", "free"),
        ("https://sandbag.be/feed/", "free"),          # EU entity
    ],
    "Ember Climate": [
        ("https://ember-climate.org/feed/", "free"),
        ("https://www.ember-climate.org/feed/", "free"),
    ],
    "ERCST": [
        ("https://ercst.org/feed/", "free"),
        ("https://www.ercst.org/feed/", "free"),
    ],

    # ── Premium source blog/public feeds ─────────────────────────────────
    "Sylvera (blog)": [
        ("https://www.sylvera.com/blog/feed/", "free"),
        ("https://sylvera.com/blog/feed/", "free"),
        ("https://www.sylvera.com/feed/", "free"),
    ],
    "BeZero Carbon (insights)": [
        ("https://bezerocarbon.com/insights/feed/", "free"),
        ("https://www.bezerocarbon.com/insights/feed/", "free"),
        ("https://bezerocarbon.com/feed/", "free"),
    ],
    # Domain confirmed via Chrome (May 2026): clearbluemarkets.com (NOT clearblue.markets)
    # Both RSS feeds confirmed working; <category>CBAM</category> tags present
    "Clear Blue Markets (knowledge-base, confirmed)": [
        ("https://www.clearbluemarkets.com/knowledge-base/rss.xml", "free"),
    ],
    "Clear Blue Markets (news, confirmed)": [
        ("https://www.clearbluemarkets.com/news/rss.xml", "free"),
    ],

    # ── Taiwan sources (confirmed working in semiconductor newsletter) ────
    "CNA Finance (confirmed)": [
        ("https://feeds.feedburner.com/rsscna/finance", "free"),
    ],
    "CNA International (confirmed)": [
        ("https://feeds.feedburner.com/rsscna/intworld", "free"),
    ],
    "Economic Daily — 產業 (confirmed)": [
        ("https://money.udn.com/rssfeed/news/1001/5588?ch=money", "free"),
    ],

    # ── Paid sources ──────────────────────────────────────────────────────
    "Financial Times — World (confirmed)": [
        ("https://www.ft.com/world?format=rss", "paid"),
    ],
    "Financial Times — Europe (unverified)": [
        ("https://www.ft.com/world/europe?format=rss", "paid"),
    ],
    "Nikkei Asia (confirmed)": [
        ("https://asia.nikkei.com/rss/feed/nar", "paid"),
    ],
    "Reuters — Environment": [
        ("https://feeds.reuters.com/reuters/environment", "paid"),
        ("https://www.reuters.com/rss/environment", "paid"),
        ("https://feeds.reuters.com/reuters/environmentNews", "paid"),  # old variant
    ],
    "Reuters — Business": [
        ("https://feeds.reuters.com/reuters/businessnews", "paid"),
        ("https://feeds.reuters.com/reuters/businessNews", "paid"),
        ("https://www.reuters.com/rss/businessnews", "paid"),
    ],
}


# ── Feed checker ──────────────────────────────────────────────────────────────

def check_feed(url: str) -> dict:
    try:
        r = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        if r.status_code != 200:
            return {"valid": False, "status": r.status_code, "url": url}

        feed = feedparser.parse(r.content)
        if not feed.entries:
            return {"valid": False, "status": r.status_code, "url": url,
                    "note": "No entries (feed parses but is empty)"}

        latest = feed.entries[0]
        title = latest.get("title", "—")
        pub = latest.get("published", latest.get("updated", "—"))
        return {
            "valid": True,
            "status": r.status_code,
            "url": url,
            "entry_count": len(feed.entries),
            "latest_title": title[:75],
            "latest_date": pub,
        }
    except Exception as e:
        return {"valid": False, "status": "error", "url": url, "note": str(e)[:80]}


def main():
    print(f"\n{'='*72}")
    print(f"  CBAM Monitor — RSS Feed Checker  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*72}\n")

    results: dict[str, dict] = {}

    for source, candidates in CANDIDATES.items():
        print(f"Checking: {source}")
        found = False
        for url, src_type in candidates:
            result = check_feed(url)
            result["source_type"] = src_type
            if result["valid"]:
                results[source] = result
                print(f"  ✅  {url}")
                print(f"      {result['entry_count']} entries | Latest: \"{result['latest_title']}\"")
                print(f"      Date: {result['latest_date']}")
                found = True
                break
            else:
                status = result.get("status", "err")
                note = result.get("note", "")
                print(f"  ❌  {url}  [{status}]{' — ' + note if note else ''}")
        if not found:
            results[source] = {"valid": False}
        print()

    # ── Summary ───────────────────────────────────────────────────────────
    working = {s: r for s, r in results.items() if r.get("valid")}
    broken  = {s: r for s, r in results.items() if not r.get("valid")}

    print(f"\n{'='*72}")
    print("SUMMARY")
    print(f"{'='*72}")
    print(f"\n✅ Working ({len(working)}):")
    for s, r in working.items():
        print(f"   {s:<42s}  {r['url']}")

    print(f"\n❌ No feed found ({len(broken)}):")
    for s in broken:
        print(f"   {s}")

    # ── Suggested RSS_FEEDS block for fetch_feeds.py ──────────────────────
    print(f"\n{'='*72}")
    print("SUGGESTED RSS_FEEDS BLOCK (paste into fetch_feeds.py)")
    print(f"{'='*72}")

    # Group working results back into the source buckets fetch_feeds.py expects
    source_map = {
        "Euractiv": ["Euractiv — Climate & Environment", "Euractiv — Trade", "Euractiv — Energy"],
        "Carbon Brief": ["Carbon Brief"],
        "Carbon Pulse": ["Carbon Pulse"],
        "E3G": ["E3G"],
        "Sandbag": ["Sandbag"],
        "Ember Climate": ["Ember Climate"],
        "ERCST": ["ERCST"],
        "Sylvera": ["Sylvera (blog)"],
        "BeZero Carbon": ["BeZero Carbon (insights)"],
        "Clear Blue Markets": ["Clear Blue Markets (knowledge-base, confirmed)", "Clear Blue Markets (news, confirmed)"],
        "中央社 CNA": ["CNA Finance (confirmed)", "CNA International (confirmed)"],
        "經濟日報 Economic Daily": ["Economic Daily — 產業 (confirmed)"],
        "Financial Times": ["Financial Times — World (confirmed)", "Financial Times — Europe (unverified)"],
        "Nikkei Asia": ["Nikkei Asia (confirmed)"],
        "Reuters": ["Reuters — Environment", "Reuters — Business"],
    }

    print("\nRSS_FEEDS: dict[str, dict] = {")
    for group_name, source_keys in source_map.items():
        feeds = [results[k]["url"] for k in source_keys if results.get(k, {}).get("valid")]
        if not feeds:
            print(f"\n    # ❌ {group_name}: no working feed found — remove or replace")
            continue
        # Determine type from first result
        src_type = results[source_keys[0]].get("source_type", "free") if results.get(source_keys[0], {}).get("valid") else "free"
        print(f'\n    "{group_name}": {{')
        print(f'        "type": "{src_type}",')
        print(f'        "method": "rss",')
        print(f'        "feeds": [')
        for url in feeds:
            print(f'            "{url}",')
        print(f'        ],')
        print(f'    }},')
    print("}")


if __name__ == "__main__":
    main()
