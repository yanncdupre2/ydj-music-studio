# YDJ Music Studio

## Status
- [ ] Planning
- [x] In Progress
- [ ] On Hold
- [ ] Retired
- [ ] Cancelled

## Project Metadata
- **Project Number:** 02
- **Folder:** `ydj-music-studio`
- **Created:** 2026-02-13
- **Portfolio Area:** Creative & Media
- **Kind:** program

## Objective

Keep a ~10k-track Apple Music DJ library continuously enriched and usable for
harmonic mixing, and build the tools that make that work fast enough to sustain.

Library management and enrichment is the ongoing work. Every other area exists
to serve it:

| Area | Role | Reference |
|---|---|---|
| **Library** | Metadata tagging, cleanup, consensus genre/year enrichment — the continuing work | `library-management/README.md` |
| **Mixer** | Harmonic + BPM-continuity playlist optimization over the enriched library | `mixer/README.md` |
| **Downloads** | YouTube acquisition, renaming, and Apple-compatible conversion | `downloads/README.md` |
| **Karaoke** | Video prep for Final Cut Pro overlay blending | `karaoke-processing/karaoke-process.md` |
| **Infra** | Shared Apple Music access, genre taxonomy, build environment, write safety | `common/README.md` |

**Why this program has no terminal state.** Music keeps arriving. Every new
track added to the library needs genre, year, BPM and key before it is
mixer-eligible, and there is no state in which the last track has been
acquired. The tools that do the work can be finished; the library they serve
cannot.

## Scope

### In Scope
- Metadata enrichment for the Apple Music library: genre, release year, BPM, Camelot key
- Consensus tagging from four sources (duplicates, LLM, web, MusicBrainz) and interactive inconsistency resolution
- A canonical 31-genre compound taxonomy (`common/genres.json`)
- Harmonic mixing optimizer using the Camelot wheel and ±1 semitone key shifts
- YouTube acquisition via yt-dlp, renaming to `Artist - Title (type)`, and MKV→MP4 / Opus→AAC conversion
- Karaoke video enhancement for FCP `screen`/`add` overlay blending, CLI plus a macOS GUI front-end
- File renaming driven by metadata tags
- Apple Music integration: bulk reads read-only; year and genre writes live and gated per track

### Out of Scope
- Real-time DJ performance tools or live mixing
- Music streaming service integration beyond metadata lookup
- Mobile apps or web interfaces
- Collaborative playlist features

These are standing exclusions, not deferrals. A program has no release to defer
them past; taking one up is a scope change, recorded here with its date.

## Why This Exists

Maintaining a DJ library of this size by hand does not scale:

- Tracks arrive with missing or wrong year, genre, BPM and key, and Apple
  Music's native tools are weak for bulk operations.
- Genre classification is subjective. Compound genres resolve it by design.
- Duplicate and variant tracks drift out of agreement with each other.
- Ordering a set for harmonic and BPM continuity by hand is slow and error-prone.
- YouTube sources and karaoke channels each need format and visual normalization
  before they are usable downstream.

## Strategy and Breakdown

Five areas, no fixed sequencing — each evolves independently. Operational detail
lives in each area's reference, linked in the Objective table above.

### Library — the continuing work
A canonical 31-genre compound taxonomy, 4-source consensus genre/year tagging,
and interactive inconsistency resolution. Live AppleScript reads and writes for
year and genre, in production use.
**Open:** audit and fill missing BPM and Camelot key; both are blocked on a
write path that does not yet exist (see Open Questions).

### Mixer — playlist optimization
Harmonic mixing and BPM continuity solved as a track-ordering optimization over
the enriched library. Emits a timestamped Markdown mix report with bridge
key/BPM hints; opt-in `--export` writes the order back as a new playlist.
**Open:** the input playlist name is still hardcoded at `mixer/mixer.py:221`.
The candidate-library tempo-break insertion path remains commented out by design.

### Downloads — YouTube media processing
yt-dlp acquisition (h264/1080p, Safari cookies) → rename using a live Apple
Music artist list → remux and audio conversion for Apple compatibility.
Essentially complete.

### Karaoke — video prep for FCP overlay
A single canonical `karaoke-process` script (bash + ffmpeg) plus a SwiftUI macOS
front-end with live previews and persisted presets. Mature and in use.

### Infra — shared utilities and safety
Shared Apple Music access (`common/`), the genre taxonomy, the Python venv and
Rust build, and library-write safety.
**Open:** a documented, tested Apple Music backup/restore workflow before
further bulk writes.

## Architecture Decisions in Force

Only decisions that still govern current behavior. Superseded reasoning lives in
Git history and `ARCHIVE/SESSION-LOG.md`.

### Compound genre taxonomy
Genres are used exactly as they appear in the library (e.g. `EDM, House, Techno`),
from a canonical list of 31 in `common/genres.json`. This dissolves the "is it
House or Techno?" ambiguity by allowing both, reflects how the music actually
overlaps, and gives an LLM a closed vocabulary to classify into without forcing
false precision. Single-genre and hierarchical taxonomies were both rejected as
poor fits for DJ use.

### Apple Music access: live AppleScript, with one remaining XML reader
Bulk reads and all year/genre writes go through live AppleScript. Reading live
removed the staleness and manual-export burden of the XML workflow.

One consumer still reads the XML export: `library-management/cleanup.py:145`
calls `load_library()`, which reads `~/YDJ Library.xml` via
`common/apple_music.py:8`. That export is absent as of 2026-09-19, so
`cleanup.py` does not run until it is re-exported. Migrating it would remove the
last manual-export dependency.

### The interactive taggers gate every write per track
`tag_tracks.py` and `resolve_tagger.py` are the supported tagging path, and both
put a blocking single-keypress prompt (`1` / `2` / `S`) in front of every live
write and honor `--dry-run`. In `tag_tracks.py` the keypress loop at `:151` and
the `--dry-run` check both precede the write at `:176` within the same loop
iteration; there is no path to the write that bypasses them. `getch()` calls
`tty.setraw()`, so these scripts require a real TTY — see
`PROJECT-LOCAL-CONTEXT.md` for how to launch them.

This guarantee covers the interactive taggers, not every writer in the tree.
Four other scripts in `library-management/` write to the live library
(`batch_update_no_copyright.py`, `update_year.py`, and two `test_update_hymn*`
scripts), each gated by a single run-level `input()` confirmation rather than
per track. None is part of the documented workflow, but all can write to the
production library, and they are precisely the kind of bulk operation the
outstanding backup/restore condition exists to cover. A fifth,
`interactive_tagger.py`, is dead code and is carried by an [infra] task.

### Track identification: artist + name, with database ID as fallback
Database IDs go stale between XML exports; searching by artist + name does not.
`update_track_metadata()` takes optional `artist` and `name` and prefers them,
falling back to database ID when they are absent or the search fails.

This is only half-applied in practice. `resolve_tagger.py` both verifies track
identity before writing and passes artist and name; `tag_tracks.py` does
neither. See Open Questions.

### Mixer: Rust engine primary, Python fallback
The optimizer's inner loop is Rust via PyO3/maturin; Python owns all I/O and
reporting and passes precomputed flat integer tables. A missing `ydj_mixer_engine`
raises `ImportError` and falls back to the pure-Python loop
(`mixer/mixer.py:13-26`), so the mixer runs on a fresh clone before the Rust
build. Dispatch is by size: `n ≤ 20` uses the Held-Karp exact optimizer
(`HELD_KARP_MAX_TRACKS = 20`, dispatched at `mixer/mixer.py:652`); above that,
time-budgeted simulated annealing. Optimization history is in
`mixer/OPTIMIZER-PLAN.md` and `mixer/DOE-ANNEALING-PARAMS.md`.

### Mixer writes are additive only
`--export` is opt-in and creates a new `Mixer output <timestamp>` playlist. It
never mutates the input playlist. On partial failure it reports added and failed
counts and does not roll back tracks already added.

### Karaoke: one canonical script, channel fit chosen by mode
`karaoke-process` is the single canonical script and binary; the CLI is the path
for batch and scripted use, the GUI for tuning. The core pipeline masks edges,
converts to grayscale, and maps three luminance bands to fixed RGB values, which
makes the output deterministic and therefore predictable under FCP `screen`/`add`
blending.

Channels are handled by choosing a mode rather than by excluding the channel:
`--invert-bands` for channels whose unsung text is brighter than sung text, and
`--no-lut` for multi-color channels where the LUT would flatten distinct singer
colors. Per-channel starting points are in `karaoke-processing/karaoke-process.md`.

### Modular structure with per-area agent context
Each area is a subfolder with its own `CLAUDE.md` for focused agent context;
shared utilities live in `common/`. This keeps the areas independently evolvable
and keeps agent context scoped to the area being worked on.

## Standing Conditions

- **Mixer:** optimizes directly from an Apple Music playlist chosen per run (not a hardcoded name) and writes the result back as a new playlist; exact optimum for n ≤ 20. *Partially met: write-back and exact n ≤ 20 ship; the input playlist name is still the literal "Mixer input" at `mixer/mixer.py:221`. Carried by a [mixer] task.*
- **Library:** <5% of the DJ library missing year/genre; BPM and Camelot key populated for mixer-eligible tracks; consistent compound-genre taxonomy. *Unmeasured as of 2026-09-19 — no audit has ever produced the percentage, so this condition cannot currently be evaluated either way. Carried by a [library] task.*
- **Downloads:** files land in Apple-compatible formats with consistent `Artist - Title (type)` names. *Satisfied and stable since 2026-04-28. Qualitative, with no automated check.*
- **Karaoke:** overlays render predictably for FCP `screen`/`add` blending across the channels in use. *Satisfied and stable since 2026-05-09. Qualitative, validated by eye per channel.*
- **Infra:** no data-loss incidents from library writes; backup/restore documented and tested. *No incidents to date. Backup/restore is unmet and carried by an [infra] task; it gates further bulk writes.*

## Inflow

- **Inflow event:** new music added to the Apple Music library that needs
  categorization — genre, release year, BPM or Camelot key. Re-running the
  tagger over already-categorized tracks is this program's own work and is
  **not** inflow.
- **Observed cadence:** not derivable from this repository. The library lives
  in Apple Music, outside the repo, and no ingestion log survives — the only
  local trace is a single tagging batch from 2026-02-13. The basis is therefore
  the stated expectation of roughly quarterly arrival, not a measurement, and
  this field should be replaced with real numbers once an ingestion log exists.
- **Dormancy horizon:** 12 months — four times the stated quarterly
  expectation, deliberately generous because there is no measured gap to
  anchor it.
- **Last inflow:** 2026-06-27 — last committed library and mix work. This is a
  proxy for arrival rather than a record of it, which is itself the gap the
  cadence field describes.

## Risks and Dependencies

### Risks
1. **Apple Music library corruption** — Impact: high; the library holds ~10,000
   tracks. Bulk reads stay read-only and every live write is gated per track.
   A documented, tested backup/restore workflow is still outstanding and gates
   further bulk writes.
2. **Genre taxonomy drift** — New genres accumulate inconsistently over time.
   LLM tagging enforces the canonical 31-genre list; periodic audits catch drift.
3. **AppleScript field coverage** — Year and genre writes are proven in
   production. BPM and Comments are read (`common/apple_music.py:213,219`) but
   have no write path anywhere in the codebase; every writer sets year and genre
   only. This blocks the BPM and Camelot-key work.

### Dependencies
- **Apple Music** — macOS-specific; the program is tied to the Apple ecosystem
- **ffmpeg/ffprobe** — required for media processing; installed via Homebrew
- **Python 3.x** — core scripting language; see `requirements.txt`
- **Rust toolchain** — required once to build `ydj_mixer_engine`; the Python optimizer is the fallback when it is not built
- **Apple Music XML export** — still required by `library-management/cleanup.py`; absent as of 2026-09-19

### External APIs
- **MusicBrainz** — integrated (`library-management/sources/musicbrainz.py`, 1 req/sec rate limit)
- Discogs, Spotify, Last.fm — considered, not integrated

## Open Questions

1. **Sub-threshold genres.** The 31-genre taxonomy covers genres with 20+ songs.
   `PROJECT-LOCAL-CONTEXT.md`, `common/README.md` and
   `library-management/CLAUDE.md` all state that smaller genres "will be
   reclassified later." No task or Standing Condition carries this. Decide
   whether to schedule, redefine, or retire the commitment.

2. **Taxonomy evolution.** How should new music styles not covered by the 31
   canonical genres be handled — periodic review and expansion, or strict
   enforcement of the existing list?

3. **BPM and Comments writes.** Whether AppleScript can write these reliably is
   unproven, and it blocks both the BPM and the Camelot-key tagging tasks.
   Carried by a [library] spike task.

4. **Track-identity protection is applied unevenly.** `resolve_tagger.py` has
   two guards: it calls `verify_track()` to confirm the database ID still
   resolves to the expected artist + name and skips on mismatch (`:93-99`), and
   it passes `artist` and `name` into `update_track_metadata()` (`:108`).
   `tag_tracks.py` has neither — it does not import `verify_track`, and its call
   at `:176` omits `artist` and `name`, so the main tagging workflow writes by
   database ID alone with no identity check. Both values are in scope at that
   call site (`:137`). Decide whether to bring the tagger up to the resolver's
   protections or to narrow the decision to the resolver.

5. **No isolated test library.** Live writes were adopted on the understanding
   that AppleScript work could be tested against a separate test library. That
   was never built; what stands in for it is the per-track keypress gate and
   `--dry-run`. Those are preview and consent, not isolation. Decide whether an
   isolated test library is still required before further write-path work.

6. **Batch update concurrency.** What is the safe model for batch updates —
   one-at-a-time, batched, or transactional?

7. **Metadata source comparison.** Which external API serves DJ-oriented music
   best, and how should rate limits be handled for large batches?

## Resources & References

- [Apple Music AppleScript Dictionary](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/)
- [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API) · [Discogs API](https://www.discogs.com/developers)
- [Mutagen](https://mutagen.readthedocs.io/) — Python audio metadata
- [beets.io](https://beets.io/) — reference music library manager
- [Camelot Wheel](https://en.wikipedia.org/wiki/Camelot_Wheel) — harmonic mixing system
- [ffmpeg Documentation](https://ffmpeg.org/documentation.html)
