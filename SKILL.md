---
name: cbam-monitor
description: >
  Reference documentation for the CBAM/carbon news fetch pipeline (sources,
  keywords, topic classification) implemented in scripts/fetch_feeds.py. The
  actual daily/weekly delivery is handled by the daily-data.yml and
  weekly-vcm.yml GitHub Actions workflows and operated via the
  carbon-news-collector skill (cowork/carbon-news-collector.SKILL.md) — use
  that skill for running RADAR, flagging stories, or compiling the weekly
  doc. Use this file when you need to know which sources are tracked, what
  keywords/topics fetch_feeds.py matches on, or how to customize them.
---

# CBAM fetch pipeline — sources, keywords, topic classification

Reference documentation for `scripts/fetch_feeds.py`, which fetches and
filters carbon border adjustment mechanism (CBAM) and related carbon-market
news across the EU, UK, Taiwan, and other jurisdictions. This script is
shared infrastructure for the current pipeline — `daily-data.yml` (Stream A,
daily CBAM digest) and `weekly-vcm.yml` (Stream B, weekly VCM digest) both
call it, then `radar/scripts/radar_process.py` re-buckets its output into
Stream A/B for email delivery.

> The standalone weekly "CBAM Global Monitor" briefing (its own workflow and
> two-tier HTML format) has been retired in favor of the Stream A/B split
> above. For day-to-day operation (RADAR/FLAG/COMPILE), see
> `cowork/carbon-news-collector.SKILL.md`.

---

## Sources

### Free sources — RSS (headline + summary + link)

| Source | Feeds | Notes |
|--------|-------|-------|
| **Euractiv** | `euractiv.com/sections/climate-environment/feed/` | Primary EU policy coverage |
| | `euractiv.com/sections/trade/feed/` | WTO/trade law angle |
| | `euractiv.com/sections/energy/feed/` | Electricity/hydrogen scope debates |
| **Carbon Brief** | `feeds.feedburner.com/carbonbrief` | Canonical FeedBurner URL (confirmed May 2026) |
| **Carbon Pulse** | `carbon-pulse.com/feed/` | Market-facing news, CBAM tracking |
| **E3G** | `e3g.org/feed/` | EU climate policy think tank |
| **Sandbag** | `sandbag.org.uk/feed/` | EU/UK industrial decarbonization |
| **Ember Climate** | `ember-climate.org/feed/` | Power sector; electricity scope |
| **Clear Blue Markets** | `clearbluemarkets.com/knowledge-base/rss.xml` | Full articles; `<category>CBAM</category>` tags; confirmed May 2026 |
| | `clearbluemarkets.com/news/rss.xml` | Company news/press releases (lower priority) |
| **中央社 CNA** | FeedBurner: finance, intworld, mainland, technology, politics | Taiwan perspective; keyword match on 碳邊境調整機制 |
| **經濟日報** | UDN money feeds (產業, 國際財經, 金融) | Taiwan export industry coverage |

### Free sources — scraped (headline + summary + link)

Both sites confirmed SSR (May 2026). `fetch_feeds.py` scrapes them automatically
via `fetch_link_pattern_source()` — no login needed for public blog/insights content.

| Source | Listing page | Article URL pattern | Notes |
|--------|-------------|---------------------|-------|
| **Sylvera** | `sylvera.com/blog` | `/blog/[slug]` | Public blog; keyword-filtered |
| **BeZero Carbon** | `bezerocarbon.com/insights` | `/insights/[slug]` | Public insights; keyword-filtered |

### Paid sources (headline + link only)

| Source | Feeds | Notes |
|--------|-------|-------|
| **Financial Times** | `ft.com/world/europe`, `markets`, `companies`, `world/asia-pacific`, `world` | Wire-level; Europe + Asia angles |
| **Nikkei Asia** | `asia.nikkei.com/rss/feed/nar` | Asia trade impact on CBAM |
| **Reuters** | `feeds.reuters.com/reuters/environment` | Climate/environment desk |
| | `feeds.reuters.com/reuters/businessnews` | Breaking wire news |

---

## Topic Classification

Articles are classified into one of eight topic buckets:

| Bucket | What goes here |
|--------|----------------|
| **EU CBAM — Policy & Implementation** | EC regulation changes, CBAM registry updates, DG TAXUD/DG CLIMA guidance, scope expansions, price of certificates, declarant obligations, embedded emissions methodology |
| **UK CBAM** | HMRC announcements, UK government consultations, UK scheme design, alignment/divergence from EU |
| **Taiwan & Export Exposure** | Impact on Taiwanese steel, aluminium, cement exporters; 工總/industry associations; 環境部/經濟部 response |
| **Industry & Trade Response** | Sector-level responses (EUROFER, European Aluminium, cement associations), company compliance strategy, equivalence determinations, exemption applications |
| **WTO & Trade Law** | WTO compatibility debates, third-country retaliation (India, China, Turkey), CBAM legal challenges, carbon pricing equivalence determinations |
| **Other Jurisdictions** | Australia, Canada, Japan, South Korea, US carbon border discussions; regional CBAM-equivalent proposals |
| **Analysis & Research** | ERCST, E3G, Bruegel, Carbon Brief deep dives; academic papers; think tank assessments |
| **Other** | Anything matching keywords not fitting above categories |

---

## Keywords

### English (matched case-insensitively)

**Core**: CBAM, carbon border adjustment, carbon border mechanism, border carbon
adjustment, carbon border tax

**Technical**: embedded emissions, CBAM certificate, CBAM declarant, CBAM
transitional, CBAM definitive, CBAM reporting, CBAM registry, CBAM scope,
CBAM equivalence, CBAM exemption, CBAM expansion, CBAM compliance, CBAM importer

**UK-specific**: UK carbon border, UK CBAM

**Trade/legal**: CBAM WTO, carbon pricing equivalence, CBAM third country, CBAM
retaliation, CBAM challenge, CBAM India, CBAM China

**Policy rationale**: carbon leakage

### Chinese (matched as-is)

碳邊境調整機制, 碳邊境調整, 碳關稅, 歐盟碳邊境, 碳洩漏, 英國碳邊境,
碳邊境 出口, 碳邊境 鋼鐵, 碳邊境 鋁業, CBAM

---

## Delivery Format

Output format, subject lines, and stream tiering (Stream A/B, TOP/HIGH/MED)
are defined in `radar/scripts/radar_process.py` and `radar/scripts/render_email.py`
— see `cowork/carbon-news-collector.SKILL.md` for the current architecture.

---

## Customization

- **Add/remove keywords**: Edit `KEYWORDS_EN` / `KEYWORDS_ZH` in `fetch_feeds.py`
- **Add sources**: Add a new entry to `RSS_FEEDS` dict in `fetch_feeds.py`
- **Add/rename topics**: Edit `TOPIC_PATTERNS` and `TOPIC_ORDER` in `fetch_feeds.py`
  (and `HIGH_KEYWORDS`/stream logic in `radar/scripts/radar_process.py` if the
  change should affect Stream A/B classification)
- **Change schedule**: `daily-data.yml` is triggered externally by cron-job.org
  (see workflow file comments); `weekly-vcm.yml` still uses a native GitHub
  `schedule:` block — edit the cron expression in the workflow file
- **Change recipients**: Update the `CBAM_RECIPIENTS` (daily) or `VCM_RECIPIENTS`
  (weekly) secret in GitHub repo settings

---

## Important Notes

- **Paid source treatment**: FT, Nikkei, Reuters — headline and link only. Do
  not summarize. Mark clearly as "behind paywall."
- **Euractiv is free**: Full summaries available. It will likely be the
  highest-volume source for EU CBAM policy coverage.
- **Clear Blue Markets**: Domain is `clearbluemarkets.com` (not `clearblue.markets`).
  RSS feed includes `<category>CBAM</category>` tags — confirmed working May 2026.
- **Sylvera / BeZero**: Scraped via link-pattern from public blog/insights pages.
  Both confirmed SSR — no JavaScript rendering needed. Max 15 article fetches per
  source per run; 0.3s polite delay between requests.
- **Carbon leakage keyword**: Intentionally broad — catches ETS reform articles
  that are directly relevant to CBAM policy context.
- **Taiwan-language sourcing**: CNA and Economic Daily match on Chinese keywords
  only. Ensure 碳邊境調整機制 and 碳關稅 are in the keyword list at all times.
- **Weekly cadence**: CBAM moves slowly enough that 7-day lookback is appropriate.
  After holidays or major events, use `--hours 336` for two-week coverage.
