---
name: cbam-monitor
description: >
  Weekly automated briefing on carbon border adjustment mechanisms (CBAM) across
  the EU, UK, Taiwan, and other jurisdictions — runs via GitHub Actions every
  Monday. Use this skill when the user asks about CBAM news, EU CBAM
  implementation, UK CBAM progress, Taiwan export exposure, CBAM trade law or
  WTO developments, or wants to check on or update the newsletter setup. Also
  trigger for casual references like "any CBAM news this week", "what's new
  with the carbon border tax", "碳邊境調整機制最新動態", or "run the CBAM monitor".
---

# CBAM Global Monitor 碳邊境調整機制週報

Fetch, filter, and deliver a weekly newsletter covering carbon border adjustment
mechanisms across all active and emerging jurisdictions — EU, UK, Taiwan export
exposure, and global developments.

## Purpose

Weekly intelligence briefing on CBAM policy developments, organized by
jurisdiction. Designed for two audiences simultaneously:

- **Expert digest**: Full summaries, keyword tags, and source attribution for
  policy depth
- **Shareable summary**: "Key Developments" section at the top — short, scannable,
  suitable for forwarding to contacts

## Operation

Runs automatically every **Monday at 08:30 Taipei time** via GitHub Actions.
The workflow fetches articles, formats the HTML newsletter, and emails it.

```bash
# Manual run from Codespace (or local machine with outbound HTTP)
cd <repo-root>
pip install -r cbam-monitor/requirements.txt

python cbam-monitor/scripts/fetch_feeds.py \
  --hours 168 --format json --output /tmp/cbam_articles.json

python cbam-monitor/scripts/format_newsletter.py \
  --input /tmp/cbam_articles.json --output /tmp/cbam_newsletter.html

# Debug: print sample unmatched entries to diagnose keyword gaps
python cbam-monitor/scripts/fetch_feeds.py --hours 168 --debug
```

Required GitHub repository secrets:
- `GMAIL_ADDRESS` — sender Gmail address
- `GMAIL_APP_PASSWORD` — Gmail App Password (not account password)
- `RECIPIENT_EMAIL` — delivery address (alec.martin@gmail.com)

To trigger a manual run: Actions → "CBAM Global Monitor — Weekly Briefing" →
Run workflow. Override hours lookback (e.g., 336 for a two-week catch-up).

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

## Output Format

### Two-tier HTML newsletter

**Tier 1 — Key Developments** (top of email, shareable):
- One lead item per non-empty topic bucket (up to 6 items)
- Each item: topic tag pill → headline link → first sentence of summary → source/date
- Green highlight box — visually distinct, works standalone as a forward

**Tier 2 — Full Briefing** (rest of email, analyst-level):
- One H2 section per topic bucket, ordered as above
- Each article: headline (linked), source + date, full summary (free) or "behind paywall" note (paid), keyword tags
- Green accent color scheme throughout

### Subject line format
```
CBAM Global Monitor | 碳邊境調整機制週報 — YYYY-MM-DD (N articles)
```

### Archive
Save HTML to: `Carbon Markets/cbam-monitor/briefings/cbam-briefing-YYYY-MM-DD.html`

---

## Customization

- **Add/remove keywords**: Edit `KEYWORDS_EN` / `KEYWORDS_ZH` in `fetch_feeds.py`
- **Add sources**: Add a new entry to `RSS_FEEDS` dict in `fetch_feeds.py`
- **Add/rename topics**: Edit `TOPIC_PATTERNS` and `TOPIC_ORDER` in both scripts
- **Change schedule**: Edit the cron expression in `briefing.yml`
- **Change recipient**: Update `RECIPIENT_EMAIL` secret in GitHub repo settings

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
