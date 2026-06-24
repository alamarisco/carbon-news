---
name: cbam-weekly-news
description: >
  Daily radar + weekly compiler for the ESTC international news roundup on CBAM
  (碳邊境調整機制) and related subjects — EU CBAM, UK CBAM, EU ETS, free allocation,
  steel/cement/aluminium/fertiliser/hydrogen, carbon leakage, plastic CBAM, Taiwan 碳費,
  and third-country trade responses. Runs in three modes: RADAR (daily triage of fresh
  candidates into a ranked shortlist), FLAG (translate a picked story, emit a paste-ready
  LINE alert, append it to the living weekly doc), and COMPILE (finalize the dated
  Traditional-Chinese .docx in ESTC house style). Use whenever the user asks to run the
  radar, 今天有什麼CBAM新聞, triage today's news, flag an article, compile/update the weekly
  國際新聞蒐集 / 每週新聞蒐集, or hands over CBAM article links.
---

# 國際新聞蒐集 — RADAR + Weekly Collector

**The authoritative, up-to-date workflow lives in the cbam-monitor repo, not in this skill.**

At the start of every run, `web_fetch`:

```
https://raw.githubusercontent.com/alamarisco/cbam-monitor/main/WORKFLOW.md
```

and follow it exactly. It contains the current RADAR / FLAG / COMPILE steps, account constants
(Drive folder IDs, repo slug), the priority model, and the .docx house style.

**To change the workflow, edit `WORKFLOW.md` in the repo and commit — do NOT edit this skill.**
This skill is an Anthropic-managed plugin: local edits are wiped on the next sync and don't reach
other machines. The repo file is the single source of truth and is identical on every device.

## Quick reference (authoritative version is WORKFLOW.md)

- **RADAR** = fetch the CI-built triage and present it. Do **not** run `radar_process.py` locally;
  CI already built today's triage with portal dedup + staleness filtering applied.
  1. `web_fetch` `.../data/radar/index.json` → read `triage_dated`.
  2. `web_fetch` `.../data/radar/<triage_dated>` → pass to `create_artifact`.
- **FLAG** = translate (house style), LINE message, append to the weekly `.docx` via the Drive
  connector + `scripts/append_story.py`, then update the ledger by firing the `flag-pick` GitHub
  dispatch (see WORKFLOW.md FLAG step 5). No local repo clone needed.
- **COMPILE** = weekly finalize via Drive connector + `scripts/build_docx.py` / `append_story.py`.

## Skill-local assets (used by FLAG/COMPILE)

- `scripts/append_story.py`, `scripts/build_docx.py`, `scripts/extract_prior_urls.py`,
  `scripts/flag_article.py` — .docx tooling + queue logging.
- `templates/weekly_template.docx` — house-style seed for a fresh week.
- `reference/sources.md`, `reference/keywords.md`, `reference/streams.md` — tracked sources,
  bilingual keywords, stream/tier mapping.

> Any `radar_process.py` bundled in this skill is **stale and unused** — RADAR output is built by
> CI. Ignore it.
