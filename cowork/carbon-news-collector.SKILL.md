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

**The authoritative, up-to-date workflow lives in the carbon-news repo, not in this skill.**

At the start of every run, `web_fetch`:

```
https://raw.githubusercontent.com/alamarisco/carbon-news/main/WORKFLOW.md
```

and follow it exactly. It contains the current RADAR / FLAG / COMPILE steps, account constants
(Drive folder IDs, repo slug), the priority model, and the .docx house style.

**To change the workflow, edit `WORKFLOW.md` in the repo and commit — do NOT edit this skill.**
This skill is an Anthropic-managed plugin: local edits are wiped on the next sync and don't reach
other machines. The repo file is the single source of truth and is identical on every device.

## Quick reference (authoritative version is WORKFLOW.md)

- **RADAR** = find the digest email → parse it → present a numbered pick-list. CI already built
  and emailed the digest (daily CBAM = Stream A, weekly VCM = Stream B) — nothing to regenerate.
  1. Gmail-search: `subject:"CBAM 每日雷達" newer_than:2d` (daily) or
     `subject:"碳權市場週報" newer_than:9d` (weekly). Fetch the **raw HTML body**, save to
     `/tmp/digest.html`.
  2. Run `python /tmp/carbon_tools/scripts/parse_digest_email.py --html /tmp/digest.html
     --out /tmp/digest.json` (fetch it first if not present — see WORKFLOW.md "Fetch tools").
     It extracts a hidden JSON payload embedded in the email (robust to Gmail
     reformatting/quoting) and prints a numbered list — present that as the pick-list.
  3. When the user picks by number or pastes a URL, proceed to FLAG mode for each.
  - Do **not** run `radar_process.py` locally — RADAR is built and emailed by CI.
- **FLAG** = translate (house style), LINE message, append to the weekly `.docx` via the Drive
  connector + the repo's `weekly/scripts/append_story.py`, then update the ledger by firing the
  `flag-pick` GitHub dispatch (see WORKFLOW.md FLAG step 5). No local repo clone needed.
- **COMPILE** = weekly finalize via Drive connector + the repo's `weekly/scripts/build_docx.py` /
  `append_story.py`.

## Assets

- **All tooling is canonical in the repo**, fetched to `/tmp/carbon_tools/` at runtime — ignore
  any copies bundled in this skill:
  - `radar/scripts/parse_digest_email.py` (RADAR)
  - `weekly/scripts/{append_story,build_docx,extract_prior_urls,flag_article}.py` +
    `weekly/templates/weekly_template.docx` (FLAG/COMPILE)
- Skill-local reference docs: `reference/sources.md`, `reference/keywords.md`,
  `reference/streams.md` — tracked sources, bilingual keywords, stream/tier mapping.

> Any `radar_process.py` or `scripts/*.py` bundled in this skill is **stale and unused** — RADAR
> is built and emailed by CI; all tools are fetched fresh from the repo. Ignore bundled copies.
