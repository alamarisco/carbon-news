---
name: carbon-news
description: >
  Reference documentation for the carbon-news fetch pipeline (sources,
  keywords, topic classification) implemented in scripts/fetch_feeds.py.
  Delivery is a single weekly email sent by the weekly-digest.yml GitHub
  Actions workflow. Use this file when you need to know which sources are
  tracked, what keywords/topics fetch_feeds.py matches on, or how to
  customize them.
---

# carbon-news pipeline — sources, keywords, topic classification

Reference documentation for `scripts/fetch_feeds.py`, which fetches and
keyword-filters carbon-market news across the EU, UK, Taiwan, Asia and other
jurisdictions. The pipeline is three scripts and one workflow:

```
scripts/fetch_feeds.py    fetch + keyword-filter + classify → latest.json
scripts/radar_process.py  dedupe + drop stale/evergreen/already-sent + order → candidates.json
scripts/render_email.py   candidates.json → email-safe HTML
.github/workflows/weekly-digest.yml   runs all three Monday morning, emails the result
```

`scripts/check_feeds.py` is a health checker — it imports the source config
from `fetch_feeds.py` and probes every feed, so it never goes out of sync.

> **Restructured July 2026.** Formerly a CBAM-specific brief with a daily
> digest (`daily-data.yml`, Stream A) plus a weekly VCM digest
> (`weekly-vcm.yml`, Stream B). Now a **single weekly carbon-news digest**:
> no Stream A/B split, no TOP/HIGH/MED priority tiers, and no CBAM-first
> ordering — items are grouped by topic bucket. Also removed: the official
> EU/UK portal scrapers (official developments now arrive via third-party
> reporting), three noisy sources (Carbon Pulse, Carbon Credits, ESG遠見), and
> the Cowork `carbon-news-collector` skill along with its FLAG/COMPILE `.docx`
> tooling and `flag-pick.yml` dispatch. The seen-URL ledger was rebuilt as a
> rolling, self-pruning one held in the Actions cache (see Delivery).

---

## Sources

Source config lives in `RSS_FEEDS` and `LINK_PATTERN_SOURCES` in
`fetch_feeds.py` — that is authoritative; the tables below are a snapshot.
Run `python scripts/check_feeds.py` to probe them all for health.

### Free — RSS

| Source | Feeds | Notes |
|--------|-------|-------|
| **Euractiv** | `euractiv.com/feed/` | Primary EU policy coverage. Section feeds are Cloudflare-blocked — main feed only |
| **Carbon Brief** | `carbonbrief.org/feed/` | Direct feed; the FeedBurner URL was hijacked May 2026 |
| **Carbon Market Watch** | `carbonmarketwatch.org/feed/` | EU carbon policy watchdog |
| **Climate Home News** | `climatechangenews.com/feed/` | International climate policy |
| **Politico Europe** | energy section + main | Energy section is the more targeted of the two |
| **E3G** | `e3g.org/feed/` | EU climate policy think tank |
| **Sandbag** | `sandbag.be/category/cbam/feed/` | EU entity; `sandbag.org.uk` is empty |
| **Clear Blue Markets** | knowledge-base + news `rss.xml` | Full articles, `<category>` tags |
| **EU Council** | press releases + `THMENV` register | Council CBAM/ETS milestones |
| **European Commission** | press corner RapidPress API (text-filtered) | EC announcements land here first |
| **EUROMETAL** | `eurometal.net/feed/` | European metals association |
| **GMK Center** | `gmk.center/en/feed/` | Ukrainian steel analytics; strong CBAM coverage |
| **The Hindu Business** | Economy feed | India trade/carbon |
| **NDTV Profit India** | FeedBurner | India business wire |
| **中央社 CNA** | FeedBurner ×5 (財經/國際/兩岸/科技/政治) | Taiwan; Chinese-keyword match |
| **經濟日報 Economic Daily** | UDN money ×4 (國際/兩岸/產業/商情) | Taiwan export industry |
| **聯合新聞網 UDN** | 要聞 feed `6638` | Other UDN category feeds return empty titles |
| **環境資訊中心 e-info** | `e-info.org.tw/rss/eic.xml` | Title-only match (feed summaries empty) |

### Free — scraped (no RSS available)

All confirmed SSR; `fetch_link_pattern_source()` collects article hrefs by
regex from a listing page (or sitemap), then fetches each for date + summary.
Max 15 article fetches per source per run, 0.3s polite delay.

| Source | Listing page |
|--------|-------------|
| **ICAP** | `icapcarbonaction.com/en/news` |
| **SteelOrbis** | `steelorbis.com/steel-news/` (RSS retired June 2026) |
| **Sylvera** | `sylvera.com/blog` |
| **BeZero Carbon** | `bezerocarbon.com/sitemap.xml` (listing page is JS-rendered) |
| **Ember Energy** | `ember-energy.org/latest-insights/` (RSS Cloudflare-blocked) |
| **Reccessary** | `reccessary.com/zh-tw` (RSS dead; Taiwan/Asia clean energy) |
| **今週刊 ESG** | `esg.businesstoday.com.tw` |
| **經貿透視 Trademag** | `trademag.org.tw` |

### Paid (headline + link only — do not summarize)

| Source | Feeds |
|--------|-------|
| **Financial Times** | `world`, `markets`, `companies`, `world/asia-pacific`, `world/europe` |
| **Nikkei Asia** | `asia.nikkei.com/rss/feed/nar` |
| **Bloomberg Green** | `feeds.bloomberg.com/green/news.rss` |
| **天下雜誌 CommonWealth** | scraped 永續發展 section (preview only) |

**Removed sources**: Carbon Pulse (subscription lapsed July 2026), Carbon
Credits (July 2026 — stock-promotion pieces flooding the VCM bucket), ESG遠見
(July 2026 — non-carbon ESG/lifestyle items), DG TAXUD CBAM + UK CBAM Portal
(portal scrapers retired July 2026), Reuters (all RSS shut down May 2026),
S&P Global (Akamai 403s), CTEE / Cnyes / CSRone / CNA Net Zero (403 or
JS-rendered), Parliament Magazine / PIK Potsdam (no RSS).

---

## Topic Classification

Articles are classified into one of eight topic buckets (consolidated from 15
in July 2026). `TOPIC_ORDER` in `fetch_feeds.py` is the section order in the
email, and is mirrored in `radar_process.py` and `render_email.py`.

| Bucket | What goes here |
|--------|----------------|
| **Compliance Carbon Markets 強制性碳市場** | All mandatory regimes in one bucket: CBAM (EU + UK, incl. sectoral scope — steel, aluminium, cement, fertiliser, hydrogen, plastics), EU ETS, UK ETS, Japan GX-ETS, Korea K-ETS, India/Turkey ETS |
| **Taiwan 台灣碳市場與綠色金融** | 碳費, TCX/台灣碳權交易所, 環境部 action, 碳盤查, plus Taiwan-anchored green finance and ESG disclosure (綠色金融行動方案, 永續分類標準, 永續報告書, 範疇三) |
| **Voluntary Carbon Market (VCM) 自願性碳市場** | VCM developments, carbon credits/offsets, registries (Verra, Gold Standard), ICVCM/CCP labels |
| **Article 6 & CORSIA 第六條與航空** | Paris Agreement Article 6.2/6.4, ITMOs, corresponding adjustments; CORSIA, aviation offsets, SAF |
| **Carbon Removal & Nature 碳移除與自然碳匯** | CDR, DAC, biochar, enhanced weathering; forest/blue/soil carbon, REDD+, nature-based solutions |
| **Industry & Trade Response 產業與貿易回應** | Carbon leakage, WTO compatibility, third-country retaliation (India, China, Turkey), equivalence/exemptions; plus hard-to-abate industry — green steel, blast furnace/EAF/DRI, EUROFER, steel & aluminium tariffs, named producers (台泥, 亞泥, Norsk Hydro) |
| **Analysis & Research 分析與研究** | ERCST, E3G, Bruegel, Carbon Brief deep dives; academic papers; think tank assessments |
| **Other 其他** | Anything matching keywords not fitting above categories |

> The former standalone "Cement, Steel & Hard-to-Abate" bucket was retired:
> CBAM-tagged sectoral terms (`cbam steel`, `aluminium cbam`, 鋁業碳關稅…) moved
> into Compliance so they stay with CBAM; the rest (decarbonisation tech,
> tariffs, named producers) moved into Industry & Trade Response.

---

## Keywords

`KEYWORDS_EN` and `KEYWORDS_ZH` in `fetch_feeds.py` are the full lists — an
article is kept if any keyword appears in its title, description, content or
tags (English case-insensitive, Chinese matched as-is). Broad coverage by
theme:

- **CBAM** — CBAM and its variants, carbon border adjustment/mechanism/tax,
  embedded emissions, certificates, declarants, registry, scope, equivalence,
  exemptions, free allocation, MRV, suspension clause, downstream extension,
  sectoral variants (plastic/aluminium/fertiliser/urea/hydrogen)
- **Compliance markets** — EU ETS, UK ETS, Taiwan 碳費, Japan GX-ETS/GX League,
  Korea K-ETS, India ETS, Turkey ETS, allowances, EUA price, cap and trade
- **VCM** — voluntary carbon market, credits, offsets, registries, ICVCM,
  Core Carbon Principles/CCP label, Verra, Gold Standard
- **Article 6 & CORSIA** — Article 6.2/6.4, ITMOs, corresponding adjustment,
  CORSIA, aviation carbon, SAF, ICAO
- **Removal & nature** — carbon removal, CDR, DAC, biochar, enhanced
  weathering, REDD+, forest/blue/soil carbon, nature-based solutions
- **Industry & trade** — carbon leakage, WTO, green steel, blast furnace, EAF,
  DRI, EUROFER, steel/aluminium tariffs, named producers
- **Taiwan green finance** — 綠色金融行動方案, 永續分類標準, 永續報告書,
  氣候相關財務揭露, 範疇三

Note `carbon leakage` / 碳洩漏 is intentionally broad — it catches ETS reform
articles that matter for policy context.

---

## Delivery

One weekly email, Monday morning Taipei (primary 09:23, backup 11:07), sent by
`weekly-digest.yml` to the `CBAM_RECIPIENTS` secret. Subject:
`Carbon News 碳市場每週彙整 — <date> (N items)`. Body is grouped by topic
bucket, newest first within each bucket.

Everything runs in `/tmp` on the runner — the workflow has
`permissions: contents: read` and writes nothing to the repo. Two pieces of
state persist in the Actions cache: `last_emailed.txt` (a date marker that
stops a backup slot double-sending) and `seen_urls.json` (the rolling ledger,
below).

**Scheduling.** cron-job.org is the primary trigger, Mondays at 09:00 Taipei.
It POSTs to the **workflow_dispatch** endpoint:

```
POST https://api.github.com/repos/alamarisco/carbon-news/actions/workflows/weekly-digest.yml/dispatches
Authorization: Bearer <PAT with actions:write>
body: {"ref":"main"}
```

Note this is `/actions/workflows/<file>/dispatches`, which takes the **workflow
file name** — so renaming the workflow file breaks the trigger and must be
mirrored in cron-job.org. (`repository_dispatch` with type `run-weekly` or
`run-daily` is also accepted, but is not what cron-job.org uses.)

The `schedule:` slots (10:07 and 11:07 Taipei) are backups, since GitHub's own
cron queues at peak minutes and can be dropped. Whichever trigger fires first
wins; the rest hit the guard and no-op.

**The guard applies to every trigger**, including the cron-job.org dispatch —
so a retry cannot double-send. To re-send on a day that already went out, run
the workflow manually with `force: true`.

**Rolling URL ledger.** `.state/seen_urls.json` maps each delivered URL to the
date it was sent, so a story lingering in a slow feed can't reappear in a later
digest. Entries age out after `LEDGER_KEEP_DAYS` (90) in `radar_process.py`,
keeping the file bounded. Crucially, `radar_process.py` does **not** write the
ledger in place — it proposes the next state in `ledger_next.json`, and the
workflow promotes that over the real ledger only after the email actually
sends. Otherwise a failed send would mark stories as seen that no one ever
received. A missing, corrupt, or old list-shaped ledger degrades to "nothing
seen yet" rather than failing the run.

`monitor.yml` checks the last successful `weekly-digest` run via the API each
Tuesday and opens a repo issue if it is more than 8 days old.

---

## Customization

- **Add/remove keywords**: Edit `KEYWORDS_EN` / `KEYWORDS_ZH` in `fetch_feeds.py`
- **Add sources**: Add an entry to `RSS_FEEDS` (has a feed) or
  `LINK_PATTERN_SOURCES` (needs scraping) in `fetch_feeds.py`, then verify with
  `python scripts/check_feeds.py "<name>"`
- **Add/rename topics**: Edit `TOPIC_PATTERNS` and `TOPIC_ORDER` in
  `fetch_feeds.py` — then mirror the new `TOPIC_ORDER` into
  `scripts/radar_process.py` and `scripts/render_email.py`, which each keep
  their own copy for ordering
- **Change schedule**: edit the cron expressions in `weekly-digest.yml`
- **Change recipients**: update the `CBAM_RECIPIENTS` secret in GitHub repo
  settings (`VCM_RECIPIENTS` is unused since the July 2026 merge and can be
  deleted)
- **Change lookback**: default is 168h (7 days). Run the workflow manually with
  the `hours` input (e.g. `336`) for two-week coverage after a holiday. Keep
  `--maxage` in the workflow at least as large as the lookback in days,
  or `radar_process.py` will drop what `fetch_feeds.py` just collected.

---

## Important Notes

- **Paid source treatment**: FT, Nikkei, Bloomberg, CommonWealth — headline and
  link only, no summary (`make_article()` blanks the summary for `type: paid`).
- **Euractiv is free**: full summaries available; likely the highest-volume
  source for EU policy coverage.
- **Clear Blue Markets**: domain is `clearbluemarkets.com` (not
  `clearblue.markets`).
- **Taiwan-language sourcing**: CNA and Economic Daily match on Chinese
  keywords only. Keep 碳邊境調整機制, 碳關稅 and 碳費 in the keyword list.
- **No official-portal scrapers**: DG TAXUD CBAM and the gov.uk UK CBAM Portal
  were retired July 2026. EU Council and European Commission remain as *RSS*
  feeds (not page scrapes) and carry Council/EC press releases; everything else
  official arrives via third-party reporting.
- **`format_html` / `format_markdown` in `fetch_feeds.py`** are leftovers from
  the retired standalone monitor. The pipeline only uses `--format json`.
