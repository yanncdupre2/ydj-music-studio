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

A comprehensive DJ music production and library management system spanning five
areas that evolve independently:

1. **Mixer** - harmonic mixing and BPM continuity using the Camelot wheel system,
   solved as a track-ordering optimization (simulated annealing + Held-Karp exact)
2. **Library** - metadata tagging, cleanup, and LLM-powered genre categorization
   for a ~10k-track Apple Music library
3. **Downloads** - YouTube acquisition, renaming, and conversion for Apple
   ecosystem compatibility
4. **Karaoke** - video enhancement for Final Cut Pro overlay blending
   (`karaoke-process` script + SwiftUI GUI front-end)
5. **Infra** - shared Apple Music access, the canonical genre taxonomy, the
   build environment, and library-write safety

*Restated 2026-09-19: this list previously named "three interconnected domains"
and omitted karaoke entirely, despite karaoke being the most-worked area in the
project's history. It now matches the five areas in Strategy and Breakdown.*

**Why this program has no terminal state.** Music keeps arriving. Every new
track added to the library needs genre, year, BPM and key before it is
mixer-eligible, and there is no state in which the last track has been
acquired. The tools that do the work can be finished; the library they serve
cannot.

## Scope

### In Scope
- Harmonic mixing optimizer using Camelot wheel and key shifting
- Apple Music library metadata analysis, read live via AppleScript (XML export retained only for `library-management/cleanup.py`)
- Duplicate/discrepancy detection and cleanup workflows
- Genre taxonomy with 31 compound categories (e.g., "EDM, House, Techno")
- YouTube media processing (MKV→MP4, Opus→AAC conversion)
- YouTube video downloading via yt-dlp (h264/1080p, Safari cookies for YouTube Premium)
- YouTube download renaming (`rename_youtube.py` — artist/title/type normalization using Apple Music library)
- Karaoke video enhancement for FCP overlay blending (`karaoke-process` script: luminance-LUT remap with optional `--no-lut` floor-to-black mode + edge masking via ffmpeg; intro/outro preserve-or-blackout, zoom in/out, inverted band polarity, outline halo, background darken, custom sung color, and a SwiftUI GUI front-end)
- File renaming based on metadata tags
- Apple Music integration: bulk reads read-only; year and genre writes live and gated per track by the interactive tagger's keypress prompt

*Two entries corrected 2026-09-19: "XML parsing" no longer describes the primary
read path (AppleScript replaced it 2026-02-15), and "safe read-only integration
(initial phase)" understated the current state - year/genre writes have been in
production since 2026-02-15.*

### Out of Scope
- Real-time DJ performance tools or live mixing
- Music streaming service integration beyond metadata lookup
- Mobile apps or web interfaces
- Collaborative playlist features

*These are standing exclusions, not deferrals. A program has no release to defer
them past; if one is ever taken up it is a scope change, recorded here with its
date. The heading previously read "Out of Scope (Initial Release)".*

## Problem Statement

As an amateur DJ (YDJ), maintaining an organized music library and creating compelling mixes involves several time-consuming challenges:

**Library Management:**
- Tracks often have missing or incorrect metadata (year, genre, BPM, key)
- Manual tagging is tedious and error-prone
- Genre classification is subjective; need consistent taxonomy (solution: compound genres)
- Apple Music's native tools are limited for bulk operations
- Duplicate/similar tracks have inconsistent tagging across library

**Playlist Optimization:**
- Creating harmonically mixed sets manually is extremely time-consuming
- Balancing BPM continuity with harmonic compatibility is complex optimization problem
- No efficient way to optimize track order for flow and energy
- Current Python mixer script works but is slow (tens of minutes for 30-song playlist)

**Media Processing:**
- YouTube downloads recently changed from .mp4 to .mkv format
- Need efficient batch conversion to Apple-compatible formats (MP4/M4A)
- Want quick preview capability on macOS (QuickLook doesn't support MKV well)

## Strategy and Breakdown

The project spans five areas with no fixed sequencing — each evolves independently.

### Mixer — playlist optimization
Harmonic mixing (Camelot wheel + ±1 semitone shifts) and BPM continuity, solved as a track-ordering optimization. Rust engine via PyO3/maturin: simulated annealing for large sets, Held-Karp exact for n ≤ 20; Python fallback when the Rust module isn't built. Reads the "Mixer input" Apple Music playlist live; emits a timestamped Markdown mix report with bridge key/BPM hints. Opt-in `--export` writes the optimized order back as a new timestamped Apple Music playlist (shipped 2026-06-27; the input playlist is never mutated).
**Open:** the input playlist name is still hardcoded (`mixer/mixer.py:221`); selecting it per run is the remaining gap in the Standing Condition below. The candidate-library tempo-break insertion path in `mixer/mixer.py` remains commented out by design.

### Library — metadata management
Consistent metadata across a ~10k-track Apple Music library: a canonical 31-genre compound taxonomy, 4-source consensus genre/year tagging (duplicates / LLM / web / MusicBrainz), and interactive inconsistency resolution. Live AppleScript reads/writes for year + genre, validated and in production use.
**Open:** audit + fill missing BPM and Camelot key.

### Downloads — YouTube media processing
yt-dlp acquisition (h264/1080p, Safari cookies) → rename to `Artist - Title (type)` using a live Apple Music artist list → MKV→MP4 remux and Opus→AAC conversion for Apple compatibility. Essentially complete.

### Karaoke — video prep for FCP overlay
`karaoke-process` (bash + ffmpeg): luminance-LUT 3-band pipeline with edge masking, intro/outro preserve-or-blackout, zoom, inverted-band polarity, outline halo, background darken, and a `--no-lut` multi-color mode, plus a SwiftUI GUI front-end with live previews and persisted presets. Mature and in use.

### Infra — shared utilities & safety
Shared Apple Music access (`common/`), the canonical genre taxonomy, the Python venv + Rust build, and library-write safety.
**Open:** a documented, tested Apple Music backup/restore workflow before further bulk writes.

## Key Decisions and Rationale

### Decision: SwiftUI GUI for karaoke-process-v2 (`karaoke-process-gui`)
**Context:** v2's CLI surface had grown to 12 flags (`-t -b -l -r -lo -hi -splash -z -f --corners-only --invert-bands --outline --sung-color`) and tuning a new channel meant editing the command line, running `-f` for a still frame, opening the PNGs in Preview, adjusting flags, repeating. Three pain points: (1) no live previews at the chosen frame; (2) no way to validate text positioning against the final aspect ratio of the output; (3) no way to capture per-channel parameter sets cleanly (e.g., "Sing King with pink sung color" vs "Sing King with orange").

**Decision:** Build a SwiftUI macOS app that drives `karaoke-process-v2 -f` for live previews and the full `karaoke-process-v2` for the final encode. Wrap it in an Automator Quick Action so it's a Finder right-click away. CLI usage of the script remains unchanged — the GUI is purely additive.

**Architecture:**
- Swift Package Manager executable target → bundled into `KaraokeProcessGUI.app` via `build.sh` (ad-hoc codesigned)
- SwiftUI views; `NSViewRepresentable` wraps `AVPlayerView` for the player (avoids a `_AVKit_SwiftUI` startup crash on macOS 26)
- Aspect-ratio-faithful white borders on all three image panels using each image's true `naturalSize × preferredTransform` (so the border traces the *real* video edges)
- Foreground `Process` for the full encode; stderr is streamed and ffmpeg's `time=HH:MM:SS.ss` parsed against the asset's loaded duration to drive a progress bar with ETA. Cancel button kills the child cleanly; closing the window cancels too.
- Persisted presets as JSON at `~/Library/Application Support/KaraokeProcessGUI/presets.json`. Seeded with `Sing King` and `Musisi` on first launch. Backward-compatible decoder (`decodeIfPresent ?? default` for every field) so future schema additions don't lose existing user presets. Splash params are intentionally NOT included in saved presets (splash is per-file).
- Color picker via SwiftUI's `ColorPicker` (defaults the shared `NSColorPanel` to Crayons mode at app launch).

**Driving v2 changes:** the GUI work surfaced two small additions to v2: (1) `-o OUTPUT_DIR` so preview PNGs land in a per-launch tmpdir, not next to the source file; (2) `--sung-color HEX` so the user can pick a sung-text color other than the hardcoded green. Filename token gets `-sungXXXXXX` only when non-default — backward-compatible for default-green workflows.

**Splash SAR fix (drove out by GUI testing):** running v2 from the GUI on a Party Tyme APT file with non-1:1 source SAR (19520:19521) hit a `Parsed_concat: Input link parameters do not match` error when zoom was enabled (zoom's `crop` filter normalizes body SAR to 1:1, but splash branch kept original SAR). Fix: explicit `setsar=1` on both concat branches. Backward-compatible — videos with already-1:1 SAR are unchanged.

**Tradeoff:** the GUI is macOS-only and adds a Swift toolchain dependency for rebuilding. CLI is still the path for batch automation, scripting, and Linux/CI use.

**Date:** 2026-05-03

### Decision: Karaoke v2 Enhancements (splash, zoom, invert-bands, outline)
**Context:** The v1 luminance-LUT pipeline (decision below) works on Musisi-style channels but had three gaps surfacing during multi-channel testing: (1) channel splash screens (artist/title intro cards) were getting LUT-quantized along with the rest of the video, destroying their original look; (2) thinner-font channels were hard to read at native scale on a music-video background; (3) channels like Party Tyme have *brighter* unsung text than sung text, so the v1 LUT polarity (`black / white / green` low→high) maps both into the wrong bands and was documented as "do not run".

**Decision:** Build a parallel v2 script (`karaoke-process-v2`) that adds:
- `-splash SECONDS` — single-pass `concat` filter inside `filter_complex`. Splash branch trims `[0,N)` and emits unaltered; body branch trims `[N,end]` and runs the mask+LUT chain; both concat. Audio stream-copied from the input → bit-perfect, no AAC frame-boundary issues. Accepts decimals.
- `-z PERCENT` — `scale=iw*z:ih*z, crop=W:H` after the mask, before the grayscale+LUT. Output dims unchanged. Filter ordering matters: LUT runs *after* the scale, so the output stays deterministic 3-color (no anti-aliased gray pixels at scaled edges).
- `--invert-bands` — flips the LUT polarity to `black / green / white` (low→high). Rescues Party Tyme and similar channels. Filename token changes `bwg-` → `bgw-` to flag the swap.
- `--outline N` (default 2; 0 disables) — stacked-offset gray copies of the LUT'd text shape in 8 compass directions: inner stamps at ±N (gray 80), outer stamps at ±2N (gray 220), composited via alpha so the colored text core is preserved. Produces a "neon double-ring" halo: bright outer ring + dark inner gasket, total 2N px wide. Adds 16 overlay stamps per frame (~3-4x slower re-encode); when N=0 the outline chain is skipped and the script uses the fast `-vf` path. Earlier attempts at outlines via `gblur+blend` and edge filters all looked poor; the stacked-copy approach is deterministic and configurable.

**Rationale:**
- Each option addresses a real channel-coverage gap, not speculative
- `-splash` and `-z` slot cleanly into the existing pipeline; `--invert-bands` is a tiny LUT swap; `--outline` reuses the same `overlay`/`colorkey` primitives we already trust
- Validated on ROSÉ & Bruno Mars - APT (Party Tyme channel): all three integrated options produce the expected output (orange→green, white→white, splash unaltered, 10% zoom, audio bit-perfect)
- v1 left untouched at `~/.local/bin/karaoke-process` until v2 is fully validated; promotion is a copy + path update

**Tradeoff:** v2 has more parameters (we now have `-t -b -l -r -lo -hi -splash -z -f --corners-only --invert-bands` and soon `--outline`). The CLI surface is broader but each flag is independent and the help text covers usage.

**Date:** 2026-05-02

**Update (2026-05-09):** v1 retired. The v2 script (with all subsequent additions — bg-darken, intro/outro preserve/blackout, `--no-lut` floor-to-black mode, negative zoom, sung-color picker, GUI) is now the single canonical `karaoke-process` script and binary. The parallel-prototype phase ended once feature parity was reached and exceeded.

### Decision: Luminance-LUT Karaoke Pipeline (replaces `geq` color-match)
**Context:** The original karaoke processing pipeline used ffmpeg's `geq` filter to do per-pixel color detection (orange → green) plus `gblur+blend` for glow. It worked visually but ran at ~0.1x realtime on 1080p — a 4-minute song took ~40 minutes to process.

**Decision:** Replace the `geq`-based pipeline with a luminance-LUT approach: convert the masked frame to grayscale (`hue=s=0`), then map three luminance bands to fixed RGB outputs using `lutrgb` — `< lo` → black `(0,0,0)`, `lo ≤ val < hi` → white `(255,255,255)`, `≥ hi` → green `(0,200,0)`. Packaged as `karaoke-process` (bash + ffmpeg), installed at `~/.local/bin/karaoke-process` for global access.

**Rationale:**
- `lutrgb` is a per-channel scalar LUT — orders of magnitude faster than `geq`'s expression evaluator
- Near realtime on 1080p (a 4-minute song now processes in minutes, not 40 min)
- Output is fully deterministic: every pixel ends up as one of three exact RGB values, which makes FCP `screen`/`add` blending behave predictably
- Built-in still-frame mode (`-f SECONDS`) emits PNGs for fast threshold/mask tuning before committing to a full re-encode
- Drops the glow stage (formerly `gblur+blend`); if a bloom is wanted, apply it as a separate FCP effect on the overlay layer
- Side benefit: no `geq` means no YUV chroma contamination concerns, so no need for the `format=gbrp` workaround

**Alternatives Considered:**
- Keep `geq`, optimize via `colorchannelmixer` / GPU acceleration / lower resolution: rejected — the LUT approach made these unnecessary
- Python + OpenCV vectorization: rejected — heavier dependency for what turned out to be a one-liner LUT in ffmpeg

**Tradeoff:** Color matching is now indirect (via luminance, not RGB ratios). Channels whose sung/unsung text don't separate cleanly by luminance (e.g., Party Tyme, where sung-green and unsung-white are both "bright" but at different luminances that the LUT would invert) are not a good fit for this tool.

**Date:** 2026-04-28

### Decision: Held-Karp Exact Optimizer
**Context:** Rust SA engine runs 3,561 attempts in 5 min but still cannot guarantee the global optimum. With 17 tracks, SA found best cost 40.5 over thousands of attempts; Held-Karp found 40.5 in 0.43s — guaranteed optimal.

**Decision:** Add Held-Karp DP optimizer in Rust alongside SA. Dispatch: n ≤ 20 → Held-Karp (exact, seconds); n > 20 → SA (probabilistic, time-budgeted).

**Rationale:**
- Held-Karp is O(n² · 2ⁿ): exponential but tractable for n ≤ 20 (< 1s for n=17, ~4s for n=20)
- Reuses the same precomputed flat integer tables as SA — zero new data structures from Python side
- SA fallback is untouched; large playlists (n > 20) continue using the 60x Rust SA engine
- For typical DJ sets (15–20 tracks), the user now gets the provably best mix instantly

**Results:** n=17 in 0.43s, n=20 in 4.2s; verified against brute-force on 20 random test cases (n=4–6); all match exactly.

**Date:** 2026-02-17

### Decision: Rust SA Engine via PyO3
**Context:** Python SA loop had been fully optimized (delta cost, integer arrays, swap-undo) but was still limited to ~80 attempts in 5 minutes for a 17-track playlist. DOE confirmed solution quality scales with attempt count, not temperature schedule.

**Decision:** Port the entire SA inner loop (including timed outer multi-attempt loop) to Rust via PyO3/maturin. Python continues to own all I/O and reporting; precomputed tables are passed as flat Python lists.

**Rationale:**
- Rust eliminates Python interpreter overhead — tight numeric loops are order-of-magnitude faster
- Zero-copy table passing: Python already had flat arrays from the Phase A optimizations
- Graceful fallback: `ImportError` falls back to the Python loop seamlessly
- DOE insight ("quality driven by attempt count") made the business case clear

**Results:** 60x throughput (0.2 → 12.0 att/s); 3,561 attempts in 5 min vs ~80 Python; better solutions found consistently.

**Date:** 2026-02-17

### Decision: Compound Genre Taxonomy
**Context:** Is a song "House" or "Techno"? Classification ambiguity causes inconsistency.

**Decision:** Use compound genres exactly as they appear in library (e.g., "EDM, House, Techno", "New-Wave, Techno-Pop, Electro-Pop, Synth-Pop")

**Rationale:**
- Solves classification ambiguity by design (both House AND Techno)
- Reflects actual music overlap (Depeche Mode = New-Wave, CHVRCHES = Synth-Pop, but very similar music)
- Enables LLMs to categorize without forcing false precision
- 31 canonical genres cover 95%+ of library

**Alternatives Considered:**
- Single-genre per track: Rejected due to classification difficulty
- Hierarchical taxonomy: Too complex, doesn't reflect DJ use case
- Free-form tags: Too inconsistent for filtering/searching

### Decision: XML Export (Read-Only) Before Direct AppleScript Integration
**Context:** Need to read/write Apple Music library metadata safely.

**Decision:** Start with XML export (read-only), defer direct write operations to Phase 4.

**Rationale:**
- Safety first: Don't risk corrupting production music library (10,000+ tracks)
- XML export is well-tested, reliable, and low-risk
- Allows development of library management tools without write risk
- AppleScript testing can happen in isolation with test library

**Alternatives Considered:**
- Direct AppleScript from start: Rejected as too risky without testing
- File-level metadata editing: Rejected because Apple Music uses proprietary database

### Decision: Python First, Rust Later for Mixer
**Context:** Current Python mixer is slow but works.

**Decision:** Enhance Python implementation first (Phase 3), port to Rust later (Phase 5).

**Rationale:**
- Python mixer is functional; performance is acceptable for now
- Focus on user experience improvements first (dynamic playlists, visualization)
- Rust port is significant effort; defer until Python version is feature-complete
- Performance optimization at Python level (algorithmic) may be sufficient

### Decision: Modular Structure with Subfolder AI Context
**Context:** Project has three distinct domains (mixer, library, downloads).

**Decision:** Separate into subfolders, each with its own CLAUDE.md for focused AI agent context.

**Rationale:**
- Clean separation of concerns
- Enables focused AI assistance within each domain
- Common utilities shared via common/ folder
- Each domain can evolve independently

### Decision: Artist+Name Search for AppleScript Track Updates
**Context:** AppleScript track updates were failing with "Can't get track" errors when using database IDs from XML export.

**Decision:** Search tracks by artist + name instead of database ID, with database ID as fallback.

**Rationale:**
- Eliminates dependency on fresh XML exports (database IDs can become stale)
- More reliable for finding the correct track in Apple Music's live database
- Backwards compatible via fallback to database ID
- Fixes ~50% failure rate in track updates

**Alternatives Considered:**
- Require fresh XML export before every operation: Rejected as manual and inconvenient
- Database ID only: Rejected due to staleness issues
- Direct AppleScript library queries instead of XML: Future enhancement, but artist+name search solves immediate problem

**Date:** 2026-02-15

## Risks and Dependencies

### Risks
1. **Apple Music Library Corruption**
   - Mitigation: bulk reads stay read-only; every live write is gated per track by the interactive tagger's keypress prompt (`library-management/tag_tracks.py:151`)
   - Outstanding: a documented, tested backup/restore workflow, which gates further bulk writes
   - Impact: High (could lose metadata for an entire 10,000-track library)

2. **Genre Taxonomy Drift**
   - Risk: over time, new genres added inconsistently
   - Mitigation: LLM auto-tagging enforces the canonical 31-genre list; periodic audits

3. **Mixer Performance Bottleneck** - *resolved 2026-02-17.* The Rust SA engine
   and the Held-Karp exact optimizer shipped; the mixer now runs to a user-chosen
   time budget rather than against a performance ceiling. Retained as the record
   of why the Rust port was undertaken.

4. **AppleScript API Limitations**
   - Risk: AppleScript may not support every metadata field the Standing Conditions require
   - Status: year and genre are proven in production. BPM and Comments are read
     (`common/apple_music.py:213,219`) but have no write path anywhere in the
     codebase - every writer sets year and genre only (`tag_tracks.py:49,53`)
   - Mitigation: spike the BPM/Comments write path before committing to the two
     tagging tasks that depend on it

*Phase-era framing removed from Risks 1, 3 and 4 on 2026-09-19. Risks describe
present exposure, so "mitigation in Phase 3/Phase 4" no longer parses. The
phase wording inside Key Decisions stays untouched, per the 2026-05-23 decision
to keep those as historical record.*

### Dependencies
- **Apple Music**: macOS-specific; the program is tied to the Apple ecosystem
- **ffmpeg/ffprobe**: required for media processing; installed via Homebrew
- **Python 3.x**: core scripting language for automation
- **Rust toolchain**: required once to build `ydj_mixer_engine`; the Python optimizer is the fallback when it is not built
- **Apple Music XML Export**: `library-management/cleanup.py:145` still reads
  `~/YDJ Library.xml` through `common/apple_music.py:8`, and that export is
  absent as of 2026-09-19 - so `cleanup.py` does not run until it is
  re-exported. Every other reader moved to live AppleScript on 2026-02-15;
  migrating `cleanup.py` would remove the last manual-export dependency.

### External APIs
- **MusicBrainz** - integrated (`library-management/sources/musicbrainz.py`,
  1 req/sec rate limit). *Moved out of "Future" on 2026-09-19; it has been one
  of the four tagging sources since 2026-02-14.*
- Discogs (vinyl/DJ metadata), Spotify (audio features), Last.fm (genre tags) -
  considered, not integrated

## Standing Conditions

- **Mixer:** optimizes directly from an Apple Music playlist chosen per run (not a hardcoded name) and writes the result back as a new playlist; exact optimum for n ≤ 20. *Partially met as of 2026-09-18: write-back and exact n ≤ 20 ship; the input playlist name is still the literal "Mixer input" at `mixer/mixer.py:221`. Carried by a [mixer] task.*
- **Library:** <5% of the DJ library missing year/genre; BPM and Camelot key populated for mixer-eligible tracks; consistent compound-genre taxonomy. *Unmeasured as of 2026-09-19 - no audit has ever produced the percentage, so this condition cannot currently be evaluated either way. The [library] metadata audit is what turns it from an assertion into a number.*
- **Downloads:** files land in Apple-compatible formats with consistent `Artist - Title (type)` names. *Satisfied and stable since 2026-04-28. Qualitative, with no automated check; treated as a settled area rather than a live commitment, and reopened only if a format or naming regression appears.*
- **Karaoke:** overlays render predictably for FCP `screen`/`add` blending across the channels in use. *Satisfied and stable since 2026-05-09. Qualitative and validated by eye per channel; treated as a settled area rather than a live commitment.*
- **Infra:** no data-loss incidents from library writes; backup/restore documented and tested. *No incidents to date. Backup/restore is unmet as of 2026-09-18 and carried by an [infra] task; it gates further bulk writes.*

*Annotated 2026-09-19: the Downloads and Karaoke conditions are qualitative and
have no test behind them. Marking them settled is deliberate - it keeps the
review honest about which conditions are actually live work (Mixer, Library,
Infra) and which are historical statements of a bar already cleared.*

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

## Open Questions

1. **Genre Taxonomy Evolution**
   - How do we handle new music styles not covered by the 31 canonical genres?
   - Should we periodically review and expand the taxonomy, or enforce a strict list?

2. **Playlist Management** - *resolved 2026-09-19.* Selecting the playlist per
   run is the answer, and it is now a Standing Condition carried by a [mixer]
   task; `mixer/mixer.py:221` still hardcodes "Mixer input". Optimizing multiple
   playlists in one invocation was considered and dropped: each run is
   time-budgeted, so batching them only splits the budget.

3. **Apple Music Integration**
   - Year and genre writes are proven and in production. **BPM and Comments are
     read but never written** - `common/apple_music.py:213,219` read them, and
     every write path (`tag_tracks.py:49,53`) sets year and genre only. Whether
     AppleScript writes them reliably is unproven, and it blocks both the BPM
     and the Camelot-key tagging tasks.
   - What is the safe concurrency model for batch updates (one-at-a-time,
     batched, transactional)?

4. **MusicBrainz/Discogs Integration**
   - Which API provides better metadata for DJ-oriented music (electronic, house, techno)?
   - How to handle API rate limits for large batch operations?

5. **Performance Target** — *resolved 2026-02-17.* The Rust port shipped and was
   worth it: a single 17-track benchmark measured 0.2 → 12.0 attempts/s, and
   Held-Karp later made n ≤ 20 exact rather than approximate. The mixer now runs
   to a user-chosen time budget (default 5 min) instead of a fixed attempt count,
   so "acceptable optimization time" is a per-run input, not an open target.

## Resources & References

- [Apple Music AppleScript Dictionary](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/)
- [MusicBrainz API Documentation](https://musicbrainz.org/doc/MusicBrainz_API)
- [Discogs API Documentation](https://www.discogs.com/developers)
- [Mutagen Library](https://mutagen.readthedocs.io/) - Python audio metadata
- [beets.io](https://beets.io/) - Reference music library manager
- [Camelot Wheel](https://en.wikipedia.org/wiki/Camelot_Wheel) - Harmonic mixing system
- [ffmpeg Documentation](https://ffmpeg.org/documentation.html)

## Notes

- **Genre Philosophy**: Compound genres solve the "is it House or Techno?" problem by allowing both
- **Safety First**: superseded 2026-02-15 — AppleScript year/genre writes are in production, gated per track by the interactive tagger's keypress prompt. XML export is still used for bulk *reads*.
- **Performance**: superseded 2026-02-17 — the Rust engine shipped and is the default path; the pure-Python optimizer now only runs as a fallback when `ydj_mixer_engine` is not built.
- **Backup**: Always backup Apple Music library before any batch metadata operations
