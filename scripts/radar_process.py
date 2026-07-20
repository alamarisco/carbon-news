#!/usr/bin/env python3
"""Digest processor — dedupe, filter and order the weekly carbon-news digest (OFFLINE only).

All web fetching is done by scripts/fetch_feeds.py BEFORE this script runs; results are
passed in as a local file. Nothing here touches the network.

Restructured July 2026: the daily CBAM digest and the weekly VCM digest merged into a single
weekly email, and the brief broadened from CBAM-specific to carbon markets generally. Priority
tiers (TOP/HIGH/MED) and the Stream A/B split are gone — items are grouped by topic bucket in
TOPIC_ORDER instead.

Inputs:
  --articles   latest.json produced by scripts/fetch_feeds.py                 [required]
  --outdir     output directory                                              [required]
  --date       run date YYYY-MM-DD (default: today, Taipei)
  --ledger     rolling seen-URL ledger to suppress repeats across weeks       [optional]

Outputs (in --outdir):
  candidates.json          — all items, bucket-ordered (machine-readable)
  weekly_digest_<date>.md  — the same list as Markdown, grouped by topic bucket
  ledger_next.json         — the ledger as it should look AFTER a successful send

The ledger is deliberately NOT written back in place. This script proposes the next ledger
state in ledger_next.json; the workflow promotes it over --ledger only once the email has
actually been sent. Writing it here would mean a failed send silently marks stories as seen
and they are never delivered.
"""
from __future__ import annotations
import argparse, json, os, re, datetime

# Topic bucket order — kept in sync with TOPIC_ORDER in scripts/fetch_feeds.py.
TOPIC_ORDER = [
    "Compliance Carbon Markets 強制性碳市場",
    "Taiwan 台灣碳市場與綠色金融",
    "Voluntary Carbon Market (VCM) 自願性碳市場",
    "Article 6 & CORSIA 第六條與航空",
    "Carbon Removal & Nature 碳移除與自然碳匯",
    "Industry & Trade Response 產業與貿易回應",
    "Analysis & Research 分析與研究",
    "Other 其他",
]
TOPIC_RANK = {t: n for n, t in enumerate(TOPIC_ORDER)}

# Preferred outlet when the same story appears in several places (dedup tie-break).
SOURCE_RANK = {
    "GMK Center": 60, "S&P Global": 60, "Euractiv": 56,
    "EU Council": 55, "European Commission": 55,
    "Clear Blue Markets": 50, "Carbon Brief": 50, "Politico Europe": 48,
    "中央社 CNA": 46, "經濟日報 Economic Daily": 46, "聯合新聞網 UDN": 44,
    "環境資訊中心 e-info": 42,
    "Financial Times": 30, "Nikkei Asia": 30, "Bloomberg Green": 30,
}

EVERGREEN_PAT = re.compile(
    r"^(what is|what's)\b|: your guide|\bexplained\b|your guide"
    r"|大哉問|懶人包|一次看|圖解|教戰守則|一文看懂|是什麼",
    re.I
)
DEFAULT_MAXAGE_DAYS = 8

# How long a URL stays in the rolling ledger. Well beyond the 7-day fetch window, so a story
# lingering in a slow feed can't reappear, while the file stays bounded (~a quarter of URLs).
LEDGER_KEEP_DAYS = 90


def load_ledger(path):
    """Return {url: first_seen_date}. Tolerates a missing or corrupt file."""
    if not path or not os.path.exists(path):
        return {}
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}
    urls = data.get("urls", {})
    # Accept the old list-of-URLs shape too, dating those entries to the epoch so they age out.
    if isinstance(urls, list):
        return {u: "1970-01-01" for u in urls}
    return urls if isinstance(urls, dict) else {}


def prune_ledger(ledger, run_date):
    cutoff = (datetime.date.fromisoformat(run_date) -
              datetime.timedelta(days=LEDGER_KEEP_DAYS)).isoformat()
    return {u: d for u, d in ledger.items() if d >= cutoff}


def is_evergreen(title, summary):
    return bool(EVERGREEN_PAT.search(title or "")) or "your guide" in (summary or "").lower()


def norm_title(t):
    t = (t or "").lower()
    t = re.sub(r"[^\w一-鿿]+", " ", t)
    return " ".join(t.split())


def dup_key(t):
    # same first 6 significant words ≈ same story across outlets (coarse on purpose;
    # Claude does the semantic same-story pass at review time)
    words = norm_title(t).split()
    return " ".join(words[:6]) if words else norm_title(t)


def bucket_key(i):
    """Position in TOPIC_ORDER; unknown buckets sort last."""
    return TOPIC_RANK.get(i.get("topic") or "Other 其他", len(TOPIC_ORDER))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--articles", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--ledger", default="",
                    help="rolling seen-URL ledger; items already in it are suppressed")
    ap.add_argument("--date", default=None)
    ap.add_argument("--maxage", type=int, default=DEFAULT_MAXAGE_DAYS,
                    help="drop items older than this many days before --date")
    a = ap.parse_args()

    run_date = a.date or datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d")
    cutoff = (datetime.date.fromisoformat(run_date) -
              datetime.timedelta(days=a.maxage)).isoformat()
    os.makedirs(a.outdir, exist_ok=True)

    arts = json.load(open(a.articles, encoding="utf-8"))
    ledger = load_ledger(a.ledger)

    kept = {}
    dropped_dupe = dropped_old = dropped_evergreen = dropped_seen = 0
    for art in arts:
        url = (art.get("link") or art.get("url") or "").strip()
        title = art.get("title", "")
        if not url or not title:
            continue
        # 0) already delivered in an earlier digest
        if url in ledger:
            dropped_seen += 1
            continue
        pub10 = (art.get("published", "") or "")[:10]
        summ = art.get("summary", "")
        # 1) drop stale items — and undated items, which we can't place in the window
        if not pub10 or pub10 < cutoff:
            dropped_old += 1
            continue
        # 2) drop evergreen "what is X / your guide" explainer pages
        if is_evergreen(title, summ):
            dropped_evergreen += 1
            continue
        cand = {
            "title": title, "summary": summ, "url": url,
            "source": art.get("source", ""), "published": pub10,
            "topic": art.get("topic", ""), "matched_keywords": art.get("matched_keywords", []),
        }
        k = dup_key(title)
        if k in kept:
            dropped_dupe += 1
            if SOURCE_RANK.get(cand["source"], 40) > SOURCE_RANK.get(kept[k]["source"], 40):
                kept[k] = cand
        else:
            kept[k] = cand

    # Two passes, relying on sort stability: newest-first within each bucket group.
    items = sorted(kept.values(), key=lambda i: i["published"], reverse=True)
    items.sort(key=bucket_key)

    json.dump(
        {"date": run_date, "items": items,
         "stats": {"total": len(items), "dupes_collapsed": dropped_dupe,
                   "dropped_stale": dropped_old, "dropped_evergreen": dropped_evergreen,
                   "dropped_already_sent": dropped_seen}},
        open(os.path.join(a.outdir, "candidates.json"), "w", encoding="utf-8"),
        ensure_ascii=False, indent=2)

    # Proposed next ledger — the workflow promotes this over --ledger only after a successful
    # send, so a failed email never buries stories that were never delivered.
    next_ledger = prune_ledger(ledger, run_date)
    next_ledger.update({i["url"]: run_date for i in items})
    json.dump({"updated": run_date, "urls": next_ledger},
              open(os.path.join(a.outdir, "ledger_next.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    write_digest(os.path.join(a.outdir, f"weekly_digest_{run_date}.md"), run_date, items, dropped_dupe)

    by_topic = {}
    for i in items:
        by_topic[i.get("topic") or "Other 其他"] = by_topic.get(i.get("topic") or "Other 其他", 0) + 1
    breakdown = " · ".join(f"{t.split()[0]} {n}" for t, n in by_topic.items())
    print(f"[DIGEST] {run_date}: {len(items)} items ({breakdown}) · "
          f"{dropped_dupe} dupes · {dropped_old} stale · {dropped_evergreen} evergreen · "
          f"{dropped_seen} already sent · ledger {len(ledger)} → {len(next_ledger)}")
    print(f"[OUT] {a.outdir}")


def write_digest(path, run_date, items, dupes):
    md = [f"# Carbon News 碳市場每週彙整 — {run_date}", ""]
    md.append(f"_{len(items)} items after dedup · {dupes} duplicates collapsed_\n")
    for topic in TOPIC_ORDER:
        group = [i for i in items if (i.get("topic") or "Other 其他") == topic]
        if not group:
            continue
        md.append(f"## {topic} ({len(group)})\n")
        for i in group:
            md.append(f"- **{i['title']}**")
            md.append(f"  {i['source']} · {i['published']}")
            if i["summary"]:
                md.append(f"  {i['summary'][:200]}")
            md.append(f"  {i['url']}\n")
    open(path, "w", encoding="utf-8").write("\n".join(md))


if __name__ == "__main__":
    main()
