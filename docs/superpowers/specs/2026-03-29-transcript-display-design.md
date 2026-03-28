# Transcript Display Redesign — Design Spec
**Date:** 2026-03-29

## Overview

Two changes to how transcripts are displayed:

1. **index.html Step II** — Remove per-segment tagging UI. Transcript becomes read-only plain text.
2. **history.html detail view** — Add a collapsible transcript section above 決議事項.

## Changes

### index.html

**Remove tagging from Step II transcript:**
- `renderSegments()` renders each segment as plain text only — no tag buttons
- Remove `setTag()` function entirely
- Remove `.tag-btn`, `.tag-btn-decision`, `.tag-btn-action`, `.segment-actions` CSS rules
- Remove `seg.tag` references throughout (segments no longer carry a `tag` field in the UI)
- In `renderSummary()`, remove the tagged-segment sections (「標記決議」and「標記待辦」blocks). The summary continues to show AI-analyzed decisions and action items unchanged.
- `reanalyze()` also calls `renderSegments()` — it will continue to work, now rendering plain text

**New segment rendering:**
Each segment is a `<div class="segment-item">` containing only a `<span class="segment-text">`. The `.segment-actions` column and all tag buttons are removed.

### history.html

**Collapsible transcript section in detail view:**
- Position: above the 決議事項 section
- Default state: collapsed
- Header: "逐字稿" with a toggle indicator (▶ / ▼)
- Content: full transcript as a `<pre>`-style block (preserves line breaks, readable font)
- If the meeting has no transcript (empty string or missing field): section is hidden entirely
- Clicking the header toggles open/closed with a smooth height transition

The transcript data comes from `meeting.transcript` in the existing meeting JSON — no API changes needed.

## No Backend Changes

Both changes are frontend-only. `storage.py` and `server.py` are not modified.

## Out of Scope

- Searching or filtering within the transcript
- Editing the transcript
- Timestamps per segment (not stored)
