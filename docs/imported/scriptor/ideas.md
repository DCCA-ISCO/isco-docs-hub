!!! info "Source"
    Imported from [`DCCA-ISCO/scriptor`](https://github.com/DCCA-ISCO/scriptor) · [View on GitHub](https://github.com/DCCA-ISCO/scriptor/blob/main/docs/IDEAS.md)

# IDEAS — Strategic Improvements

Higher-level architectural ideas and design directions. Concrete implementation notes live in [WIP.md](WIP.md).

---

## ~~Agenda Mapper: Escalate to Stronger Model on Low Coverage (2026-04-18)~~ DONE

Implemented 2026-04-25 (see WIP.md). Three-model escalation chain (flash → 3.1-pro → 2.5-pro) with best-so-far tracking. Fires only when coverage <50% after strict retry. Open question on UI escalation button left open — MappingView model selector serves the same purpose.

---

## Streaming Pipeline Status to the Frontend (2026-04-18)

### Goal

When the React frontend kicks off a transcription job, stream live status updates from the backend so the user can see what's happening during the long-running pipeline (typical 10-25 min wall on L4 for 2-hour meetings). Without this the UI is just a spinner — users have no signal that progress is being made or which phase is currently running.

### What to stream

Pipeline phases, each with sub-progress where meaningful:

- **FFmpeg** — extracting audio (% complete based on duration)
- **Silence detection + condense** — silence regions found, condensed length vs original
- **Gemini extraction** — model name, upload progress, generation in flight, token usage
- **NeMo alignment** — chunk N of M, energy boundary snaps, words aligned so far
- **Diarization** — pyannote / hybrid / NeMo, speaker count emerging
- **Voiceprint enrollment** — speakers enrolled (which ones)
- **Refinement (Pro pass)** — turns reviewed, corrections proposed
- **Voiceprint validation** — confirmed / disputed / reverted counts
- **Intro detection** — recording detected (start/end timestamp)
- **Speaker matrix verification** — per-VTT-speaker accuracy as it computes
- **Export** — DOCX / JSON written

Plus low-rate "activity" updates during long phases (Gemini wait): elapsed time, last log line, estimated time remaining.

### Transport options

1. **Server-Sent Events (SSE)** — natural fit, one-way server→client, works through proxies, EventSource API in browser. Lowest infrastructure cost.
2. **WebSocket** — bidirectional (overkill if client doesn't need to push), but useful if cancel/pause is added later.
3. **Polling** (`GET /jobs/{id}/status`) — simplest, but high latency and chatty.

SSE is the recommended starting point. Upgrade to WebSocket if cancel/interactive features land.

### Backend wiring

The pipeline already has a `progress_callback` parameter in `async_main(args, progress_callback)` (cli.py:455) that takes `(stage, pct, msg, **stats)`. CLI mode passes None; FastAPI wrapper would pass a function that pushes to the per-job event queue.

`logger.info` calls throughout the pipeline are also good progress signals — could be intercepted via a per-job log handler that filters relevant lines and pushes them to the same queue.

For per-job isolation with concurrent transcriptions, each job needs its own queue/channel keyed by job_id (Firestore-stored).

### Frontend UX sketch

A vertical timeline with checkmarks for completed phases, a spinner on the active phase, and a progress bar where applicable. Active phase shows the latest log line below the bar. Completed phases collapse to a one-line summary (e.g. "Aligned 8,743 words across 12 chunks in 47s").

Could also show a live-updating speaker-count badge ("8 speakers detected so far"), enrollment list ("Enrolled: Diana, Sheri, Darryn"), and final outputs list with download buttons.

### Dependencies / sequencing

Presumes the FastAPI wrapper is built (CLAUDE.md Phase 2: "FastAPI async: wrap ffmpeg calls with asyncio.create_subprocess_exec(), run alignment in run_in_executor() to avoid blocking the event loop"). The progress_callback hook already exists in CLI; the FastAPI wrapper just needs to provide an SSE-pushing implementation.

Estimated effort: 1-2 days once FastAPI wrapper exists. SSE endpoint + per-job queue + frontend timeline component.

---

## Priority Reframing: Speaker ID Over Timestamps (2026-04-07)

### Context

Transcript output feeds the minutes generator module. Minutes are summarizations of actions, motions, and votes — correct speaker attribution is critical for determining who made a motion and who seconded. Timestamps are secondary: needed only for UX navigation (click-to-play in embedded audio player), not for minutes content. "Close enough" timestamps for good navigation UX are sufficient.

### Implication

WIP.md's "Timestamp Alignment Improvements" section frames the problem as timestamp quality. The actual priority is **speaker identification accuracy**, even at the cost of more processing time, expense, or AI tokens. The NeMo aligner adoption was the right call — stable confidence, 100% success rate — but further aligner upgrades are low priority vs speaker ID gains.

### Gemini Observation

Gemini produces noticeably better text quality and speaker identification when timestamps are not requested. The model can focus its full attention budget on text accuracy and speaker attribution rather than maintaining an internal clock. This is the design rationale behind Hybrid mode's no-timestamp prompt: let Gemini do what it's best at (text + speaker ID), and add timestamps via NeMo in a post-processing step.

---

## NeMo Diarizer as Pyannote Alternative (2026-04-12)

### Status (2026-04-13)

Fully functional with 3-scale config. Batch tested on 3 meetings (2 Nursing, 1 Medical) against pyannote.

### Results

NeMo beats pyannote on nursing meetings (5 agrees each vs 1-2 for pyannote) but loses on medical (2 agrees vs pyannote's 5). Neither diarizer dominates across all meeting types. NeMo is ~20-25% slower than pyannote.

### Advantages Confirmed

- **TitaNet embeddings**: 3-scale config finds correct speaker count better than 2-scale
- **Single vendor**: NeMo already used for alignment — consolidates ML dependencies
- **No HuggingFace gated model dependency**: TitaNet/MarbleNet are open NGC models, no token required

### Remaining Issues

- **Speaker map fragmentation**: NeMo maps multiple clusters to the same speaker (e.g. 4 clusters -> Carrie Oliveira). Pyannote has the same issue. Both need the dominant-name detection logic in `build_speaker_map()` to handle this.
- **Meeting-dependent quality**: NeMo excels on nursing (large rooms, clear speakers) but underperforms on medical (more rapid exchanges, remote participants). May reflect different acoustic characteristics.

### Decision

Not replacing pyannote as default. Consider offering `--diarizer nemo` as an alternative for users to A/B test on their specific meeting types. A hybrid approach (run both, compare, take consensus) is a future option but adds complexity.

---

## Unified Post-Pipeline Validation Layer (2026-04-07, updated 2026-04-12)

### Concept

VTT correction and segment re-transcription are **post-pipeline** operations. They don't care how the transcript was produced — they operate on the output: a word list with `{word, speaker, start, end}`. This means they should be a single shared layer that all three modes (Full, Hybrid, Direct) feed into.

```
Mode-specific pipeline (Full / Hybrid / Direct)
    |
    v
[{word, speaker, start, end}, ...]
    |
    v
Unified post-pipeline validation/correction
    |
    v
Corrected output -> DOCX / JSON / minutes
```

### Current State (2026-04-12)

| Capability                    | Full | Hybrid | Direct |
|-------------------------------|------|--------|--------|
| VTT drift analysis            | Yes  | Yes    | Yes    |
| VTT timestamp correction      | Yes  | Yes    | No     |
| VTT speaker overlay           | Yes  | Yes    | Yes    |
| Voiceprint enrollment/matching| Yes  | Yes    | Yes    |
| Clip validation (Chirp)       | Yes  | Yes*   | Cross-val |
| Segment validation (Flash)    | Yes  | Yes    | Yes    |
| Importance classification     | Yes  | Yes    | Yes    |
| Pyannote enrichment           | N/A  | Yes    | Yes*   |
| Segment re-transcription      | No   | No     | No     |

*Hybrid uses Flash-based segment validation rather than Chirp clips. Direct enrichment skips text splitting (no word-level granularity); name normalization + per-turn confidence only.

Full and Hybrid are nearly at parity. Direct mode is the gap — it skips all post-pipeline validation because it doesn't load waveforms or run local models. For Direct mode, load waveform only when `--validate` is set.

### Goal

All rows "Yes" across all columns. Segment re-transcription (sliding windows + tiered escalation) is the remaining unbuilt capability.

---

## Tiered Referee Escalation (2026-04-07)

### Concept

Don't run expensive models on everything. Start cheap, escalate only on disagreement.

**Tier 1 — Flash only (cheap, covers ~85% of segments).** Re-transcribe with Gemini Flash. If text and speaker agree with pipeline, stamp as verified. Cost: one API call per segment.

**Tier 2 — Disagreement escalation.** Flash disagrees with pipeline on speaker or text ordering. Bring in referees:
- **Gemini 3.1 Pro** — different model, different failure modes
- **Chirp** — text-only tiebreaker, CTC-based ASR, decorrelates Gemini biases

**Tier 3 — Majority vote.** Pipeline + Flash + Pro + Chirp = four opinions. Three-way agreement overrides the dissenter.

### Current Partial Implementation

Segment validation (Flash Lite) runs as Tier 1 via `--validate`. Classifies segments as agree/partial/disagree. Batch results show most meetings get 4-6 agrees, 3-5 partials, 0-2 disagrees. Two outlier meetings (med-20250213: 7 disagrees, nurs-20250403: 6 disagrees) would benefit from Tier 2 escalation.

### Optimal referee selection by dispute type

- **Speaker ID dispute:** Flash + Pro + pyannote (three independent speaker signals)
- **Text content dispute:** Flash + Chirp (Chirp decorrelates Gemini biases)
- **Ordering dispute:** Flash + Pro (both see full segment context)

### Cost efficiency

Tier 2 only fires on disagreement. At current batch rates (~85% pass Tier 1), Pro/Chirp would run on ~2-4 segments per meeting — negligible cost.

---

## Speaker ID Improvements (2026-04-07, updated 2026-04-12)

### Completed

- **VTT speaker overlay**: `overlay_vtt_speakers()` corrects 943-2,176 words per meeting using Zoom channel IDs. Deployed in hybrid and full modes.
- **Voiceprint enrollment**: `enroll_from_rollcall()` extracts wespeaker embeddings from roll-call clips. `identify_speaker()` resolves disputed attributions via cosine similarity. Batch tested — corrected 63-66 words in Nursing Feb 2026.
- **Pyannote enrichment**: In hybrid mode, pyannote runs independently and splits interjections within Gemini turns. 97-99% speaker agreement. Batch tested: 129-723 splits per meeting, zero false merges after `_are_name_variants()` fix.
- **Per-turn speaker confidence**: `_speaker_confidence` in `enrich_with_pyannote()` — high/low classification based on Gemini-vs-pyannote agreement.

### Still TODO

**Multi-Pass Gemini Speaker Refinement** — Run Gemini twice: first pass gets transcript, second pass verifies/corrects speaker attributions on rapid exchanges and interjections. Cost: one extra Gemini call. Directly targets speaker ID accuracy.

**Namelist-Aware Speaker Guidance** — When Gemini produces a name that closely matches a namelist entry (e.g. "Dr. Jaffee" vs canonical "Michael Jaffe"), prefer the canonical spelling. The namelist is **not a closed set** — unlisted speakers must still appear. This is spelling normalization, not identity locking.

**Speaker Matrix Verification (P1)** — Compare VTT speaker names against pyannote clusters to catch fragmentation/confusion errors. Biggest uncovered validation gap. Blocked on VTT files (not available for most meetings).

---

## Importance Classification (2026-04-11)

### New Capability

Two-pass importance tagging on transcript turns:

1. **Regex pass**: keyword matching for motions, votes, amendments, approvals, etc. Fast, catches ~25-45% of important turns.
2. **Flash Lite pass**: sends all turns to Gemini Flash Lite for classification. Validates regex tags (confirms 56-100%), adds new tags regex missed (3-58 per meeting).

### Batch Results

Flash Lite consistently finds important turns that regex cannot — policy discussions, procedural decisions, substantive testimony. Low token cost (Flash Lite is cheapest model). Tags flow into JSON export for minutes generator consumption.

### Next

- Use importance tags to weight segment validation — prioritize validating important turns
- Feed importance classification to minutes generator for section prioritization
- Consider caching: same meeting re-processed shouldn't re-classify if transcript unchanged

---

## Interactive vs Post-Transcription Speaker Verification (future)

### Concept

During or after transcription, play a short audio clip to the user and present a dropdown of likely speaker names for verification. Could resolve the speaker fragmentation problem (multiple clusters mapping to one person) and low-confidence attributions that automated matching can't resolve.

### The Right Question: What Does Interactivity Add Over Post-Editing?

Mid-pipeline interactivity (pausing the pipeline to ask the user) would require architectural changes — the pipeline is currently a batch process. But a **post-transcription review UI** could offer the same verification step without changing the pipeline:

1. Pipeline runs in batch, produces transcript with confidence scores
2. Review UI presents low-confidence speaker attributions with audio clips
3. User verifies/corrects, corrections feed back into the speaker map
4. Corrected map is reusable for future meetings with the same participants

Post-transcription editing can do everything mid-pipeline interaction can, while keeping batch mode viable for the first pass. The pipeline already produces the signals needed to drive a review UI: `_speaker_confidence`, importance tags, and the speaker map with alternatives and confidence scores.

### When Interactivity Would Genuinely Help

The one scenario where mid-pipeline interaction beats post-editing: **voiceprint enrollment during first meeting**. If the pipeline could pause during roll call and ask "Is this Speaker A?" while the audio is fresh, it builds a voiceprint bank for all future meetings. Post-transcription can do this too, but the UX is better when the roll call is happening live.

### Decision

Defer. Post-transcription review UI is the right first step — it's compatible with batch mode and doesn't require pipeline architecture changes. Phase 2's React frontend is the natural home for this. The transcript JSON already contains everything needed (`speaker_map.json` alternatives, confidence scores, word timestamps for clip extraction).

---

## Action Validator: Fuzzy Phrase Matching (2026-04-15)

### Context

Action validator's phrase containment check currently uses exact substring matching on normalized text. This works when comparing two Gemini transcriptions of the same audio (same vocabulary), but could produce false negatives if:
- Gemini spells a name differently across runs ("Combs" vs "Coombs")
- A synonym is used ("deny" vs "reject", "defer" vs "table")
- Minor word-order variation in the motion phrasing

### Idea

Replace or augment exact phrase containment with fuzzy matching:
- **Levenshtein distance** on individual key phrases (catch spelling variants within edit distance 1-2)
- **Character n-gram overlap** (3-grams or 4-grams) for more robust partial matching
- Threshold: if a phrase matches at >80% character n-gram overlap, count it as a hit

Low priority — the current exact matching should work for most cases since both transcriptions come from Gemini hearing the same audio. Monitor false negative rate in production before investing.

---

## Voiceprint Validation Improvements (2026-04-16)

### Context

Batch-tested voiceprint validation of Pro-on-Flash speaker refinement corrections. Of 66 auto-applied corrections on nurs-20260205, voiceprint confirmed 3, disputed 3, and couldn't evaluate 60 (35 inconclusive + 25 not found). The confirmed/disputed ratio is useful but coverage is poor.

### Completed

- **Three-tier enrollment**: VTT roll-call (remote), pyannote-confirmed (room, 80%+ agreement), Gemini-turn fallback (longest monologue per unenrolled speaker)
- **Post-refinement validation**: auto-applied corrections checked against voiceprint bank, disputed corrections reverted
- **Canonical name normalization**: Gemini-turn enrollment normalizes names (e.g. "Carrie Oliveira Chair" → "Carrie Oliveira", "EO Chin" → "Amy Chin")
- **Suggestion validation**: `include_suggestions=True` validates both auto-applied and suggested corrections

### Improvements TODO

**1. Multi-clip enrollment averaging** — Currently enrolls from a single longest monologue. If that clip has bad acoustics (far from mic, HVAC), enrollment is poisoned. Average embeddings from top 3-5 longest turns per speaker. The turn-finding loop already identifies all turns — keep the top N instead of single best.

**3. High cross-similarity flagging** — When two speakers have cross-similarity > 0.30 (Amy Chin / Shari Wong at 0.40 on nurs-20260205), voiceprint can't reliably distinguish corrections between them. Auto-flag those corrections as "unreliable — similar voices" instead of claiming confirmed/disputed.

**4. Prefer early-meeting enrollment clips** — nurs-20260205 enrolled Carrie Oliveira from 7330s (post-exec session). Audio characteristics shift over long meetings (mic drift, room acoustics after breaks). Prefer enrollment clips from the first 30 minutes.

**5. Short-turn padding** — 7 of 66 corrections were inconclusive because turns were < 1s. Pad clips ±0.3s if adjacent words belong to the same speaker (no boundary crossing). A 0.7s turn padded to 1.3s is better than no data.

---

## Structured-Data + Template Architecture for High-Structure Document Parts (2026-05-03)

### Context

Header generation went through three rounds of prompt-engineering fixes (centered vs table layout, blue heading text, duplicate numbering, blank-line spacing) and was still flaky. Root cause: every layout decision was being routed through Gemini's autonomy. Different model runs would produce different structures, and what worked for one board's style would regress for another.

Shipped 2026-05-03 (commit 7528de9): replaced "LLM produces final HTML" with "LLM extracts typed values → pure-Python template renders layout" for the header. New `header_template.py` module, two layout templates (centered_block for HJUP, two_column_table for Nursing), `TitleBlockStyle.layout` discriminator on the per-board profile.

Properties this gives us:
- Layout is unit-testable as pure functions; no LLM in the loop. 18 of the 22 new tests are pure unit tests on the renderers.
- Layout never regresses on a new model run.
- Per-board layout changes are 5-line edits to a template function.
- LLM's job becomes structured extraction, which works far more reliably than HTML generation compliance.

### Where this should expand

The header was the highest-value first cut because it's the most-visible and highest-variance part of the document. Same pattern applies to other high-structure parts:

1. **Attendance lists** — currently the LLM produces "Lane Nishioka (Island Insurance)" formatting at the per-member string level. The schema captures the formatted string. If member format becomes inconsistent across runs, split the per-member format into structured fields (`name`, `affiliation`, `title`) and template the rendering.
2. **Motions** — `style_spec.motions.template` already exists as a template string. A motion-detection pass could extract `mover`, `seconder`, `action`, `result` from transcript turns and fill the template. Currently motions come out of free-form section narrative.
3. **Adjournment** — single passive-voice sentence with the time. Trivial to template once the time is extracted.
4. **Closing / Next Meeting / Sign-off blocks** — boilerplate with substitutions.

The principle: **anything where the layout is fixed and only the values change → template it. Anything genuinely free-form (discussion narrative, presentation summaries) → leave to the LLM.**

### When to extend the schema

Defer until a third layout case appears that doesn't fit `centered_block` or `two_column_table`. Premature spec extension creates surface area without demand.

### Spec extraction extension (out-of-scope follow-up)

`extract_style_structured` (the board-profile extractor) doesn't yet auto-populate `title_block.layout`. For HJUP we set it manually. When more boards get added and the manual setting becomes annoying, extend the extractor's prompt to detect layout signals from the exemplars (centered headers vs table layouts).

---

## Light / Dark Mode Toggle (2026-05-30)

### Status

Deferred (post-UAT). Evaluated, not started. Want: a user-facing light/dark
theme toggle for the React frontend.

### Why it's non-trivial today

The frontend was built dark-only with the dark palette hardcoded directly into
class names — there is no theming layer to toggle. Snapshot (2026-05-30):

- Tailwind v4 (`@import "tailwindcss"`), ~20-23 component files.
- ~678 hardcoded `slate-*` neutral utilities (backgrounds, borders, text) and
  ~980 total palette-shade utilities across 23 files.
- Zero `dark:` variants anywhere — nothing is theme-aware.
- Body bg/text hardcoded in `index.css` (`#0a0e1a` / `#e2e8f0`).
- ~60 inline `hex/rgba` colors, mostly the accent palettes in `lib/colors.ts`
  (agenda/speaker colors with `rgba(...,0.15)` fills tuned for a dark bg).

The toggle *control* is trivial; the cost is that the neutrals are literal
values in ~700 places with no abstraction to swap.

### Recommended approach — semantic token layer

1. Define CSS variables (`--bg`, `--surface`, `--surface-2`, `--border`,
   `--text`, `--text-muted`, `--accent`) in `:root` (light) and `.dark` (dark).
2. Expose them through Tailwind v4's `@theme` as utilities (`bg-surface`,
   `text-muted`, ...).
3. Find/replace the hardcoded slate scale to those tokens.
4. Toggle = flip a `.dark` class on `<html>` + persist to `localStorage` +
   honor `prefers-color-scheme`.
5. Audit accent shades + inline `rgba` fills for light-bg contrast (confidence
   highlights, amber warnings, faint `text-slate-500/600` transcript body,
   gutters).

Rejected alternative — `dark:` variant pairs (brute force): Tailwind's `dark:`
assumes light is the default; here it's inverted, so you'd rewrite the base to
light and add a `dark:` override on essentially every neutral (~678 edits, high
error rate, no reusability).

### Effort

- Toggle mechanism: ~1-2 hrs (trivial).
- Token layer + map ~678 neutrals to semantic tokens: ~2-3 days.
- Contrast audit of accents + inline fills: ~0.5-1 day.
- Per-screen QA in both themes (setup, transcript review, mapping, workspace,
  proofing, dashboard, gate) + regression fixes: ~0.5-1 day.
- **Total: ~3-5 days** polished; ~2 days for "good enough" (neutrals tokenized,
  accents mostly as-is).

The driver is the find/replace + per-screen contrast QA, not the toggle. It's a
wide, low-depth change touching almost every component's `className`.

### Recommendation

Defer past the Tuesday UAT — large-surface, broad visual QA, high regression
risk on the deadline, and dark mode is acceptable for an internal tool. If light
mode becomes firm, adopt the token layer **incrementally**: introduce semantic
tokens now and convert screens as they're touched, so the eventual toggle is a
small final step rather than a ~700-edit cliff.

---

## Unify the two HTML→DOCX renderers (2026-05-31)

**Status:** Deferred (post-UAT). Hardening, not a live bug.

DOCX export currently has **two parallel HTML→DOCX paths with separate tag
whitelists** in `generation/minutes.py`:

- `DocxBuilder(HTMLParser)` — renders top-level content (flat-layout boards).
- `_render_cell_content()` — renders content inside table cells, used by the
  `two_column_label` layout (e.g. Board of Nursing, Stock Profile) and by
  header/attendance tables.

**Why it matters:** the two lists drift. The 2026-05-31 bug (`<h2>`/`<ul>`/`<li>`
leaking as literal text in cells) happened because the cell renderer's
whitelist omitted headings/lists while `DocxBuilder` handled them. Fixed by
adding those tags to the cell renderer + stripping the redundant leading
section-title `<h2>` in `_assemble_minutes_html`. But the **bug class remains**:
any tag neither path handles (`<blockquote>`, `<a>`, `<hr>` in a cell, nested
`<table>`, `<s>`, etc.) will still leak in cells. The LLM prompt forbids `<h2>`
yet emitted it anyway — so defensive rendering, not prompt compliance, is the
right guarantee.

**Proposal:** Collapse to a **single HTML→DOCX renderer** (one source of truth)
that both the top-level body and table cells call. Likely: parse once with
BeautifulSoup/html5lib into a node tree, walk it emitting paragraphs/runs, and
make cell rendering a recursive call into the same walker (cells just target a
cell's paragraph instead of the document). Then any supported tag renders
identically everywhere, and adding a new tag is a one-place change.

Effort: ~0.5 day + DOCX test coverage for the cell path (currently lighter than
the top-level path). The existing `tests/test_docx_export.py` (40 tests) is the
safety net for the refactor.

---

## Profile-formatted Preview (Proofing) view (2026-05-31)

**Status:** Deferred (post-UAT). Nice-to-have; not blocking.

**Want:** The Proofing/Preview view should show the minutes close to what the
DOCX will look like (two-column label layout, indentation, lists, fonts).
Today it only shows bold titles + paragraph breaks; the header looks right
(it's fully-structured HTML) but the sections look unstructured.

**Why:** `ProofingView` concatenates `header_draft_html` + each
`item.draft_html` into a generic `prose` TipTap editor. It does NOT use the
DOCX assembly (`api._assemble_minutes_html`), so it skips the
`two_column_label` table layout and the `style_spec` (label width, font,
spacing, lists).

**Viability:** High — the DOCX assembly emits real HTML (borderless
`label | content` tables, `<h2>`, `<ul><li>`, `<strong>`), which a browser
renders natively. No new rendering engine needed.

**Recommended approach (single source of truth):**
1. Add `GET /api/meetings/{id}/preview-html` returning
   `_assemble_minutes_html(state, board_spec)` — the exact HTML the DOCX is
   built from.
2. `ProofingView` fetches it and renders **read-only** (the current editor's
   edits aren't even saved) in a page-like container, with CSS approximating
   the document: label-column width from
   `style_spec.sections.label_width_inches`, borderless table, the spec's
   font/size/margins, list bullets, paragraph spacing.

This keeps preview and DOCX in lockstep (one assembly fn → no drift). Pairs
naturally with the "Unify the two HTML→DOCX renderers" entry: one HTML
pipeline could feed both preview and DOCX.

**Rejected:** re-implementing the assembly in TS (duplication/drift); rendering
the actual `.docx` via `docx-preview`/`mammoth` (new dep, ~1–2 days, overkill).

**Effort:** ~0.5–1 day; the bulk is CSS to make it look document-like.

**Fidelity caveat:** HTML/CSS gets structurally close but not pixel-perfect to
Word (page breaks, tab stops, exact fonts differ). The preview would also show
real `<ul>` bullets/headings, whereas the DOCX flattens cell content to "- "
lines + bold — so cells may look slightly nicer in the preview than the DOCX.

---

## Implementation Priority (updated 2026-05-03)

Transcription pipeline:
1. ~~**Set `--refinement-model` default to Pro** — Done.~~
2. ~~**Voiceprint improvements** — Done.~~
3. **NeMo enrichment re-evaluation** — Infrastructure shipped 2026-04-17. Awaiting batch results.
4. **Speaker matrix verification** (P1) — blocked on VTT availability.
5. ~~**Investigate high-disagree meetings** — Largely resolved 2026-04-17.~~
6. ~~**Direct mode validation** — Done 2026-04-17.~~
7. ~~**`cli.py` refactoring** — Done 2026-04-25.~~
8. ~~**Agenda mapper escalation** — Done 2026-04-25.~~
9. **Streaming pipeline status to frontend (SSE)** — deferred. The big remaining transcription UX win. Scoped in a separate IDEAS entry.
10. **Segment re-transcription** — sliding windows + tiered escalation for unresolved disputes.

Minutes generation:
11. ~~**Genai SDK v2.0 migration prep** — Done 2026-04-30.~~
12. ~~**Test infrastructure bootstrap** — Done 2026-05-02. Started at 0 tests; now at 90.~~
13. ~~**Per-meeting filelock for session updates** — Done 2026-05-02.~~
14. ~~**MAX_TOKENS auto-recovery + user signaling** — Done 2026-05-03 (commit 129c4f1, 1c130ee, dc21ad9). Auto-retry with larger budget; HTTP 507 if even larger budget truncates; chat surfaces partial response with warning banner.~~
15. ~~**Print → logger conversion in `generation/`** — Done 2026-05-03.~~
16. ~~**Input validation on minutes-gen forms** — Done 2026-05-03.~~
17. ~~**Structured-data + template header generation** — Done 2026-05-03 (commit 7528de9). See separate IDEAS entry on extending this pattern to attendance/motions/adjournment.~~
18. **Extend templates to attendance / motions / adjournment** — see "Structured-Data + Template Architecture" entry above. Apply the same pattern when those areas show variability.
19. **Spec extraction → auto-populate `title_block.layout`** — defer until a third board profile makes manual setting annoying.

Phase 2 frontend hardening:
20. ~~**Transcription proxy graceful degradation** — Done 2026-05-02.~~
21. ~~**SSO auth to replace beta X-User-Id headers** — separate work, needs MS AD coordination.~~ (still TODO; not started)
22. **Streaming pipeline status (SSE)** — see #9.
23. **Light/dark mode toggle** — deferred post-UAT. Needs a semantic token layer (~3-5 days); see "Light / Dark Mode Toggle" entry above.
24. **Container width consistency across centered screens** — deferred post-UAT (noted 2026-06-01). The centered/wizard screens use inconsistent max widths: `routes/setup.tsx` (New Meeting, 3 occurrences) and `routes/meeting-setup.tsx` are `max-w-2xl` (~672px); `routes/dashboard.tsx`, `routes/boards.tsx`, and `components/AgendaReview.tsx` are `max-w-3xl` (~768px). The narrow 2xl on New Meeting truncates the selected filename (e.g. "Board of Nursing 20251106_Recordi...") even though the page has ample empty width. Fix: standardize all centered screens on ONE wider token (suggest `max-w-4xl`, ~896px) — ideally via a shared `<PageContainer>` wrapper so the width lives in one place and can't drift again — and confirm the `FileDropZone` file-row layout (filename + Remove) no longer over-truncates at that width. The Workspace stays full-width (3-panel) by design and is out of scope. Audit the remaining centered screens too: `AttendeesReview`, `TranscriptReview`, `MappingView`, `ProofingView`. **Effort:** ~20-30 min for a quick unify (bump the ~6 `max-w-*` classes to one value, low risk); ~1-2 hrs for the shared-container refactor + full audit.

---

## Tooling Notes

- **MARP** (marp.app) — slide-show presentation of ideas straight from markdown. Worth evaluating for project status decks.
