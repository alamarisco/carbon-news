#!/usr/bin/env python3
"""Feed health checker for cbam-monitor.

Probes every source configured in fetch_feeds.py (RSS_FEEDS + LINK_PATTERN_SOURCES) and
reports HTTP status, entry count, and freshness. Run from the GitHub Actions runner (or any
host with outbound HTTP) to confirm feeds before relying on them.

    python scripts/check_feeds.py            # all sources
    python scripts/check_feeds.py ICAP "ESG遠見"   # only named sources (substring match)

Flags: FAIL (4xx/5xx/error), EMPTY (0 entries), STALE (newest item > 30 days old).
Note: some outlets block datacenter or residential IPs differently — a FAIL here may still
work from the runner (and vice-versa). The authoritative check is a live daily-data run.
"""
import sys, time, concurrent.futures as cf, importlib.util, os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ff", os.path.join(HERE, "fetch_feeds.py"))
ff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ff)

import requests
try:
    import feedparser
except ImportError:
    sys.exit("feedparser required: pip install feedparser")

H = ff.HTTP_HEADERS
STALE_DAYS = 30


def _latest(entries):
    latest = None
    for e in entries:
        for f in ("published_parsed", "updated_parsed"):
            p = getattr(e, f, None)
            if p:
                dt = datetime.fromtimestamp(time.mktime(p), tz=timezone.utc)
                if latest is None or dt > latest:
                    latest = dt
                break
    return latest


def probe_rss(name, url, extra=None):
    h = dict(H); h.update(extra or {})
    try:
        r = requests.get(url, headers=h, timeout=15)
        d = feedparser.parse(r.content)
        n = len(d.entries)
        latest = _latest(d.entries)
        age = (datetime.now(timezone.utc) - latest).days if latest else None
        return (name, "rss", r.status_code, n,
                latest.date().isoformat() if latest else "no-date", age, url)
    except Exception as e:
        return (name, "rss", "ERR", 0, str(e)[:32], None, url)


def probe_scrape(name, url):
    try:
        r = requests.get(url, headers=H, timeout=15)
        return (name, "scrape", r.status_code, len(r.content), "—", None, url)
    except Exception as e:
        return (name, "scrape", "ERR", 0, str(e)[:32], None, url)


def main():
    only = sys.argv[1:]

    def want(name):
        return not only or any(o.lower() in name.lower() for o in only)

    tasks = []
    for name, cfg in ff.RSS_FEEDS.items():
        if not want(name):
            continue
        for u in cfg.get("feeds", []):
            tasks.append(("rss", name, u, cfg.get("feedparser_headers")))
    for name, cfg in ff.LINK_PATTERN_SOURCES.items():
        if not want(name):
            continue
        u = cfg.get("listing_url") or cfg.get("sitemap_url")
        if u:
            tasks.append(("scrape", name, u, None))

    rows = []
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        futs = [ex.submit(probe_rss, n, u, eh) if k == "rss"
                else ex.submit(probe_scrape, n, u) for k, n, u, eh in tasks]
        for f in cf.as_completed(futs):
            rows.append(f.result())

    print(f"\n{'SOURCE':30} {'KIND':>6} {'CODE':>4} {'N':>5} {'LATEST':>10} {'AGE':>4}  FLAG")
    print("-" * 78)
    fails = 0
    for name, kind, code, n, latest, age, url in sorted(rows, key=lambda x: x[0].lower()):
        flag = ""
        if code == "ERR" or (isinstance(code, int) and code >= 400):
            flag = "FAIL"; fails += 1
        elif kind == "rss" and n == 0:
            flag = "EMPTY"
        elif age is not None and age > STALE_DAYS:
            flag = f"STALE {age}d"
        print(f"{name[:30]:30} {kind:>6} {str(code):>4} {n:>5} {str(latest):>10} {str(age):>4}  {flag}")
    print(f"\n{len(rows)} feeds checked · {fails} failing")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
