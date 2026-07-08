---
name: carbon-news-collector
description: >
  Collects and packages carbon/CBAM news for the ESTC international news roundup —
  CBAM (碳邊境調整機制), EU CBAM, UK CBAM, EU ETS, free allocation,
  steel/cement/aluminium/fertiliser/hydrogen, carbon leakage, plastic CBAM, Taiwan 碳費,
  third-country trade responses, plus the broader VCM/carbon-credit market. The daily CBAM
  digest and weekly VCM digest are emailed automatically by CI; this skill runs three modes:
  RADAR (find that day's/week's digest email, parse it, present a numbered pick-list),
  FLAG (translate a picked story, emit a paste-ready LINE alert, append it to the living
  weekly doc), and COMPILE (finalize the dated Traditional-Chinese .docx in ESTC house
  style). Use whenever the user asks to run the radar, 今天有什麼CBAM新聞, check today's/this
  week's carbon news, triage the digest, flag an article, compile/update the weekly
  國際新聞蒐集 / 每週新聞蒐集, or hands over CBAM/carbon-market article links.
---

# Carbon News Collector — RADAR + Weekly Compiler

Daily triage and weekly compilation for the 產品碳洩漏管理與公眾溝通計畫 international news brief.
News is collected by CI continuously, alerted to the LINE group as it is picked, translated into
the **living weekly doc**, and finalized as a dated `.docx` each week.

> **Delivery is email-only.** The daily CBAM digest (Stream A) and the weekly VCM digest
> (Stream B) are emailed automatically by GitHub Actions in the `carbon-news` repo — there is
> no triage page and no file output to fetch. **RADAR mode = search Gmail for that email, parse
> it, present a numbered pick-list.** Then FLAG/COMPILE work as usual.

**Scripts are fetched fresh from the repo at runtime** (see "Fetch tools" below) since they're
executable code, not instructions — this file is self-contained for everything else. If a
script bundled directly in this skill folder is ever stale, ignore it; always re-fetch.

---

## Account constants

| Key | Value |
|---|---|
| Repo slug | `alamarisco/carbon-news` |
| Drive folder — weekly docs `國際新聞蒐集/2026年/` | `1dwXqv1UMclM1Ni3CIPBMBo62X-W58aFr` |
| Drive folder — state `國際新聞蒐集/_state/` | `1DKzbo0r0j_7jQmPd9dzB8fTNtMA5RhTX` |

### Fetch tools — once per session
```
mkdir -p /tmp/carbon_tools/scripts /tmp/carbon_tools/templates
base="https://raw.githubusercontent.com/alamarisco/carbon-news/main"
curl -sSL -o /tmp/carbon_tools/scripts/parse_digest_email.py "$base/radar/scripts/parse_digest_email.py"
for f in scripts/append_story.py scripts/build_docx.py scripts/extract_prior_urls.py \
         scripts/flag_article.py templates/weekly_template.docx templates/queue_template.md; do
  curl -sSL -o "/tmp/carbon_tools/$f" "$base/weekly/$f"
done
```
Run everything from `/tmp/carbon_tools/scripts/...`. RADAR only needs `parse_digest_email.py`;
FLAG/COMPILE need the rest. Skill-local reference docs (resolve in this skill's folder):
`reference/sources.md`, `reference/keywords.md`, `reference/streams.md` — tracked sources,
bilingual keywords, stream/tier mapping.

---

## Three modes

| Mode | When | What it does |
|---|---|---|
| **RADAR** | daily/weekly ("run the radar", "今天有什麼CBAM新聞") | Find the CI-emailed digest, parse it, present a numbered pick-list in chat. |
| **FLAG** | when the user picks items (or pastes a link) | Translate (house style), emit a paste-ready 中文 LINE message, append to the living weekly doc, log the pick, update the ledger via GitHub dispatch. |
| **COMPILE** | end of week | Top-up sweep, verify, finalize the dated `.docx` in Drive `2026年/`. |

**Architecture, briefly:** GitHub Actions (`daily-data.yml` weekday mornings ~08:23 Taipei;
`weekly-vcm.yml` Monday) fetch feeds, run RADAR processing, and email the digest — entirely in
`/tmp` on the runner, nothing written to the repo. The dedup seed is `state/seen_urls.json` in
the repo; FLAG appends to it via the `flag-pick` dispatch (step 5 below).

---

## RADAR mode — search the digest email, parse it, present picks

Both digests are rendered with a hidden, machine-readable item list embedded as an HTML comment
(`<!--RADAR_ITEMS_JSON:[...]-->`) right before the closing tag — invisible to a human reader,
trivial to parse deterministically. **Always parse via this payload, not by reading the visible
HTML** (Gmail forwarding/quoting reformats markup, but the comment survives).

| | Daily — CBAM core (Stream A) | Weekly — VCM / 廣義碳市場 (Stream B) |
|---|---|---|
| Subject prefix | `CBAM 每日雷達 — <date> …` | `碳權市場週報 …` |
| Cadence | weekday mornings | Mondays |
| Grouped by | tier (TOP/HIGH/MED) | topic |

### R1 — Find the email (Gmail connector)
Search for the most recent match:
- Daily: `subject:"CBAM 每日雷達" newer_than:2d`
- Weekly: `subject:"碳權市場週報" newer_than:9d`

Fetch the **raw/full HTML body** of that message (not the plain-text snippet, not a
quoted/forwarded re-render) and save it to `/tmp/digest.html`.

### R2 — Parse it (deterministic — don't eyeball the HTML)
Fetch `parse_digest_email.py` if not already in `/tmp/carbon_tools` (see "Fetch tools" above),
then:
```
python /tmp/carbon_tools/scripts/parse_digest_email.py --html /tmp/digest.html --out /tmp/digest.json
```
This extracts the embedded JSON and also prints a numbered plain-text list
(`1. [TOP] headline / source · date / url`, etc.) — paste that directly into chat as the
pick-list. Exit code 2 means the wrong content was fetched (re-check R1 — likely a quoted/
plain-text copy without the hidden marker).

### R3 — Hand off to FLAG
When the user picks by number (or pastes a URL directly, which still works), look up the
corresponding item's `url`/`title`/`source`/`published` in `digest.json` and proceed to
**FLAG mode** for each.

### If no matching email is found
CI opens a repo issue if the daily digest hasn't run in >26h. The user can re-run
`daily-data.yml` (or `weekly-vcm.yml`) from the GitHub Actions tab, then retry R1 after it
completes (~2 min).

### Date-verification (still applies at FLAG time)
Before shortlisting a picked story, if a date looks off, `web_fetch` the article and confirm
`meta article:published_time`. (See COMPILE Step 2.5 traps — republish ≠ original date.)

---

## FLAG mode (on pick — one article at a time)

For each picked URL:

0. **Resolve an openable source first (paywalled picks).** Several feeds give a headline +
   short summary but lock the full article: **Carbon Pulse**, Financial Times, Nikkei Asia,
   Bloomberg, and sometimes S&P Global. If the picked item is from one of these (or any page you
   cannot fully read), do **not** translate from the snippet — `WebSearch` the same story from an
   openable outlet and switch to it before translating:
   - Search the headline's key facts (e.g. `EU CBAM draft rules onerous importers June 2026`),
     preferring `reference/sources.md` names that are openable: GMK Center, S&P Global (free
     items), Euractiv, EUROMETAL, Reuters/AP reprints, Argus, Montel, official EU/UK pages.
   - **Verify it's the same story, not just the same topic:** same event/announcement, same key
     figures, and a publication date within ~1–2 days of the Carbon Pulse item (watch the
     republish-date trap in COMPILE Step 2.5).
   - Translate, cite (`新聞出處`/LINE 來源), and ledger the **openable** URL. Add the original
     Carbon Pulse URL to the dedup ledger too (FLAG step 5) so it won't resurface.
   - If no openable equivalent exists, translate from the Carbon Pulse headline + summary only,
     keep it short, and note `（僅摘要，原文需訂閱）` so Alec knows it's snippet-based.

1. **Translate** to Traditional Chinese, ESTC house style, full article (not a summary).
   For multi-section pieces, use **bold sub-headers** — but **do NOT bold body text**. Keep
   figures, company names, official titles, CN codes accurate.
   - **Body:** acronyms (CBAM, EU ETS, MRV, MSR, CSCF, DRI, EAF) may stay in Latin on first
     mention with a Chinese gloss.
   - **Titles — no acronyms.** In both the `# headline` and the LINE `中文標題`, spell every term
     out in full Chinese: 碳邊境調整機制 (not CBAM), 歐盟排放交易體系 (not EU ETS), 監測、報告與查證
     (not MRV). Organisation names use the full Chinese name — e.g. 歐洲汽車供應商協會 (not CLEPA),
     歐洲鋼鐵協會 (not EUROFER), 美國戰略暨國際研究中心 (not CSIS). Acronyms may appear later in the body.

   **繁體中文（台灣用語）house style — REQUIRED.** Translate into **Taiwanese Mandarin**, using
   Taiwan conventions and terminology, **not** PRC usage — including technical terms. Common
   swaps: 軟體 (not 軟件), 資料/數據 (not just 數據 PRC-style), 品質 (not 質量), 影片 (not 視頻),
   雷射 (not 激光), 訊號 (not 信號), 業者/廠商/鋼廠 (not 生產商). Domain-preferred TW renderings:
   排放交易體系/系統 (EU ETS), 免費配額 (free allowances), 碳洩漏 (carbon leakage),
   碳邊境調整機制 (CBAM), 直接還原鐵 (DRI), 電弧爐 (EAF), 市場穩定準備機制 (MSR),
   鋼鐵保障措施 (safeguard), 預設值 (default value), 碳費 (Taiwan carbon fee).
   **Consult Appendix A** (bottom of this file) for the full PRC→TW glossary before translating,
   and **extend it** when new terms come up. Body stays plain (no bold); sub-headers bold.

2. **Paste-ready LINE message** (Alec copies this into the LINE group). Blank line after the
   title, blank line after the summary, source + URL together at the end:
   ```
   【CBAM新聞】<中文標題>

   <一到兩句中文重點>

   來源：<媒體>｜<YYYY/MM/DD>
   <URL>
   ```

3. **Append to the living weekly `.docx`** (Drive connector → local → Drive). First fetch the
   weekly tools (see "Fetch tools" above) if not already in `/tmp/carbon_tools`:
   - Download the most recent `.docx` from Drive folder `1dwXqv1UMclM1Ni3CIPBMBo62X-W58aFr` to
     `/tmp/weekly.docx` (or seed a fresh week by copying
     `/tmp/carbon_tools/templates/weekly_template.docx` — never a blank `Document`, or the page-1
     index table and page-number footer go missing).
   - Write the translation to `/tmp/content.txt`: `# headline`, `## sub-header`, plain body lines,
     `SRC <url>`, `DATE <YYYY/MM/DD>`.
   - Run `python /tmp/carbon_tools/scripts/append_story.py /tmp/weekly.docx /tmp/content.txt /tmp/weekly_out.docx`.
     It adds a hyperlinked **項次 row** to the index table, inserts a **page break**, applies the
     item house style (新聞標題 auto-numbered 24pt; body/sub-headers Times New Roman + 標楷體 14pt,
     23pt exact line spacing, 9pt space-before; sub-headers bold, **body never bold**), and
     recalculates `本週共計 N 則`. (`/tmp/carbon_tools/scripts/build_docx.py` is for a full
     from-scratch rebuild only.)
   - Re-upload `/tmp/weekly_out.docx` to Drive folder `1dwXqv1UMclM1Ni3CIPBMBo62X-W58aFr`.

4. **Log the pick to the queue.** Run `python /tmp/carbon_tools/scripts/flag_article.py
   --root "<Drive root local path>" --week <MM.DD-MM.DD> --url URL --source S --date YYYY/MM/DD
   --by "Claude" --headline "中文標題"`, then upload the updated `_queue_<week>.md` to Drive `_state/`.

5. **Update the dedup ledger** via GitHub dispatch (no local clone; works from any machine):
   ```
   curl -X POST \
     -H "Authorization: Bearer $(gh auth token)" \
     -H "Content-Type: application/json" \
     https://api.github.com/repos/alamarisco/carbon-news/dispatches \
     -d '{"event_type":"flag-pick","client_payload":{"urls":["<URL>"]}}'
   ```
   Requires `gh` authenticated on this machine (`gh auth status`). If `gh` is unavailable,
   substitute `$CBAM_GH_TOKEN` (fine-grained PAT, Contents: read/write on `carbon-news`). The
   `flag-pick.yml` Action appends the URL to `state/seen_urls.json` and commits automatically.

Skip silently if the URL is already in the ledger or queue.

---

## COMPILE mode (weekly finalize)

The living doc is already mostly built, so this is a light pass.

### Step 1 — Establish the week & dedupe set
Download the most recent `.docx` from Drive `2026年/` to find the previous end date. Coverage
window starts the day AFTER it (includes the weekend) through this file's end date. Filename label
follows `MM.DD-MM.DD` (weekdays). Build the dedupe set from `.../state/seen_urls.json` plus the
previous 4–6 weekly files (`/tmp/carbon_tools/scripts/extract_prior_urls.py`; fetch the tools
first — see "Fetch tools" above).

### Step 2 — Top-up sweep
Read `stories_<week>.json` from Drive `_state/`. Optionally `web_fetch` tracked sources in
`reference/sources.md` for anything missed, date-restricted. A bare "CBAM" search is not
sufficient — many in-scope stories (EU ETS, 免費配額, steel safeguard, Taiwan 碳費/電力排碳係數,
塑膠版CBAM, India–EU FTA) never contain the literal "CBAM". Drop anything in the dedupe set.

### Step 2.5 — Verify every new candidate's date (REQUIRED)
`web_fetch` and read the real `published_time` before shortlisting. Traps: republish/aggregator
date ≠ original (EUROMETAL republishes SteelOrbis/Kallanish days later); a 「…13日」 headline is an
event day, not the publication month; cross-check substance against recent editions, not the URL.

### Step 2.6 — Prefer a reliable, openable source
When a story runs across outlets, choose the most reliable openable version (prefer
`reference/sources.md`: GMK Center, S&P Global, Carbon Pulse, Euractiv, EUROMETAL). Avoid
SEO/crypto reposts. Use that source's own date.

### Steps 3–6 — Translate top-ups, assemble, verify, upload
Build on `/tmp/carbon_tools/templates/weekly_template.docx` and append with
`/tmp/carbon_tools/scripts/append_story.py` (preferred), or full-rebuild with
`/tmp/carbon_tools/scripts/build_docx.py` reproducing the House style below. Verify: every
story has a working `新聞出處` URL + confirmed `日期`; no duplicates; `本週共計 N 則` matches the
count; the page-1 index table has one hyperlinked row per story; the footer shows page numbers;
spot-check 1–2 translations. Upload to Drive `2026年/`, remind Alec to copy it to the company
Drive, and present with `present_files`.

### House style
Every weekly is built on **`weekly_template.docx`** (page-1 title block + empty 項次 index table
+ centred page-number footer + the `新聞標題` numbered-list style already defined). Seed each new
week by copying `/tmp/carbon_tools/templates/weekly_template.docx`, then add stories with
`/tmp/carbon_tools/scripts/append_story.py`.

**Page 1, top (in order):**

| Element | Font | Size | Bold |
|---|---|---|---|
| Title line 1 `產品溫室氣體排放強度建立及碳邊境調整機制推動計畫` | 標楷體 / Times New Roman | 18pt | yes |
| Title line 2 `因應計畫內容蒐集國際間最新推動資訊定期更新` | 標楷體 / Times New Roman | 18pt | yes |
| Date line `YYYY年M月D日更新` | 標楷體 / Times New Roman | 14pt | no |
| Count line `本週共計 N 則` (則 bold) | 標楷體 / Times New Roman | 16pt | 則 only |

**Index table** (`項次` | `標題`), directly under the count line on page 1:
- 2-column table, 24pt exact line spacing, cells vertically centred.
- Header row `項次` / `標題`: centred, **bold**, 16pt 標楷體.
- One data row per story: `項次` centred non-bold 16pt; `標題` left-aligned, rendered as an
  **internal hyperlink** (colour `0563C1`, single underline) jumping to that article's headline
  (bookmark `art<N>`). Column widths ≈ 988 / 8646 dxa.

**Each article:**
- Starts on a **new page** (page break before every article, including the first).
- Headline: style `新聞標題`, **auto-numbered** (1, 2, 3 …), 24pt exact line spacing. No acronyms.
- Sub-headers: 標楷體 / Times New Roman 14pt **bold**, 23pt exact line spacing, 9pt space-before.
- Body / `新聞出處：<url>` / `日期：<YYYY/MM/DD>`: 14pt, 23pt exact line spacing, **never bold**,
  no first-line indent.

**Footer (every page):** centred page number — a `PAGE \* MERGEFORMAT` field.

---

## Priority model (used by CI's RADAR ranking — reference only)

- **🔴 TOP** — any NEW EU/UK official-portal item.
- **🟠 HIGH** — EU CBAM policy · **UK CBAM policy** · Taiwan exposure (碳費, 電力排碳係數,
  steel/cement/aluminium exporters) · covered goods (鋼鐵/水泥/鋁/化肥/氫/塑膠版CBAM) · industry
  & trade response · WTO & third-country (India, China, Turkey).
- **🟡 MED** — tangential CBAM mentions, market-price notes, secondary commentary.
- **Stream B (reference only, NOT triaged)** — VCM, compliance markets, CORSIA, CDR, Article 6,
  nature-based, Japan/Korea domestic ETS. Listed for research; never alerted or added to the
  weekly doc.

See `reference/streams.md`, `reference/sources.md`, `reference/keywords.md` (in this skill) for
the full bucket → stream/tier mapping, tracked sources, and bilingual keyword set.

---

## Appendix A — 繁體中文（台灣用語）glossary

Consulted by FLAG-mode translation (step 1). Translate into **Taiwanese Mandarin**, never PRC
usage — including technical terms. **Extend this table** whenever a new PRC→TW swap or domain
term comes up (edit and re-save this skill in Cowork).

### PRC → TW general swaps

| PRC usage | Taiwan usage |
|---|---|
| 生產商 | 業者／廠商／鋼廠 |
| 信號 | 訊號 |
| 軟件 | 軟體 |
| 質量 | 品質 |
| 數據 | 資料（或數據，視語境 / per context） |
| 視頻 | 影片 |
| 激光 | 雷射 |
| relining（高爐 / blast furnace） | 翻修 |
| steelmaker | 鋼廠／鋼鐵業者 |

### English → preferred TW domain rendering

| English term | Taiwan rendering |
|---|---|
| EU ETS (Emissions Trading System) | 歐盟排放交易體系／系統 |
| free allowances / free allocation | 免費配額 |
| carbon leakage | 碳洩漏 |
| CBAM (Carbon Border Adjustment Mechanism) | 碳邊境調整機制 |
| DRI (direct reduced iron) | 直接還原鐵 |
| EAF (electric arc furnace) | 電弧爐 |
| MSR (Market Stability Reserve) | 市場穩定準備機制 |
| safeguard (measure) | 鋼鐵保障措施／保障措施 |
| default value | 預設值 |
| Taiwan carbon fee | 碳費 |

Keep acronyms (CBAM, EU ETS, MRV, MSR, CSCF, DRI, EAF) in Latin on first mention with a Chinese
gloss; titles spell terms out in full Chinese (no acronyms); body never bold; sub-headers bold.
