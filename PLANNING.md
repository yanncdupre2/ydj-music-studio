# YDJ Music Studio

## Status
- [ ] Planning
- [x] In Progress
- [ ] On Hold
- [ ] Completed

## Project Metadata
- **Project Number:** 02
- **Folder:** `ydj-music-studio` (permanent identifier)
- **Original Name:** DJ Music Library Manager
- **Current Name:** YDJ Music Studio
- **Created:** 2026-02-13
- **Last Renamed:** 2026-02-13
- **Todoist Project ID:** 6ghVHmCJ3F5RJHhq
- **Todoist Project Name:** YDJ Music Studio
- **GitHub:** https://github.com/yanncdupre2/ydj-music-studio

## Vision and Scope

A comprehensive DJ music production and library management system encompassing three interconnected domains:

1. **Intelligent Playlist Optimization** - Harmonic mixing and BPM continuity using Camelot wheel system and simulated annealing
2. **Automated Library Management** - Metadata tagging, cleanup, and LLM-powered genre categorization for Apple Music library
3. **Efficient Media Processing** - YouTube download, conversion, karaoke video enhancement, and optimization for Apple ecosystem compatibility

### In Scope
- Harmonic mixing optimizer using Camelot wheel and key shifting
- Apple Music library XML parsing and metadata analysis
- Duplicate/discrepancy detection and cleanup workflows
- Genre taxonomy with 31 compound categories (e.g., "EDM, House, Techno")
- YouTube media processing (MKV→MP4, Opus→AAC conversion)
- YouTube video downloading via yt-dlp (h264/1080p, Safari cookies for YouTube Premium)
- YouTube download renaming (`rename_youtube.py` — artist/title/type normalization using Apple Music library)
- Karaoke video enhancement for FCP overlay blending (`karaoke-process` script: luminance-LUT remap with optional `--no-lut` floor-to-black mode + edge masking via ffmpeg; intro/outro preserve-or-blackout, zoom in/out, inverted band polarity, outline halo, background darken, custom sung color, and a SwiftUI GUI front-end)
- File renaming based on metadata tags
- Safe read-only Apple Music integration (initial phase)

### Out of Scope (Initial Release)
- Real-time DJ performance tools or live mixing
- Music streaming service integration beyond metadata lookup
- Mobile apps or web interfaces
- Collaborative playlist features

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
Harmonic mixing (Camelot wheel + ±1 semitone shifts) and BPM continuity, solved as a track-ordering optimization. Rust engine via PyO3/maturin: simulated annealing for large sets, Held-Karp exact for n ≤ 20; Python fallback when the Rust module isn't built. Reads the "Mixer input" Apple Music playlist live; emits a timestamped mix with bridge key/BPM hints.
**Open:** export the optimized order back to Apple Music as a new playlist.

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
   - Mitigation: Read-only XML approach initially; extensive testing in Phase 4; backup requirements
   - Impact: High (could lose metadata for entire library)

2. **Genre Taxonomy Drift**
   - Risk: Over time, new genres added inconsistently
   - Mitigation: LLM auto-tagging enforces canonical 31-genre list; periodic audits

3. **Mixer Performance Bottleneck**
   - Risk: Python optimization may not be sufficient; Rust port required sooner
   - Mitigation: Performance profiling in Phase 3; consider algorithmic improvements first

4. **AppleScript API Limitations**
   - Risk: AppleScript may not support all metadata fields we need
   - Mitigation: Research in Phase 4; fallback to XML workflow if necessary

### Dependencies
- **Apple Music**: macOS-specific; project tied to Apple ecosystem
- **ffmpeg/ffprobe**: Required for media processing; must be installed via Homebrew
- **Python 3.x**: Core scripting language for automation
- **Apple Music XML Export**: Manual export required; need to keep up-to-date

### External APIs (Future)
- MusicBrainz API (release dates, genres)
- Discogs API (vinyl/DJ metadata)
- Spotify API (audio features, genres)
- Last.fm API (genre tags, similar artists)

## Success Criteria

- **Mixer:** optimizes directly from an Apple Music playlist name (no hardcoding) and writes the result back as a new playlist; exact optimum for n ≤ 20.
- **Library:** <5% of the DJ library missing year/genre; BPM and Camelot key populated for mixer-eligible tracks; consistent compound-genre taxonomy.
- **Downloads:** files land in Apple-compatible formats with consistent `Artist - Title (type)` names.
- **Karaoke:** overlays render predictably for FCP `screen`/`add` blending across the channels in use.
- **Infra:** no data-loss incidents from library writes; backup/restore documented and tested.

## Open Questions

1. **Genre Taxonomy Evolution**
   - How do we handle new music styles not covered by 31 canonical genres?
   - Should we periodically review and expand taxonomy, or enforce strict list?

2. **Playlist Management**
   - What's the best UX for specifying which playlist to optimize? (CLI arg, interactive picker, config file?)
   - Should mixer support multiple playlists in one run?

3. **Apple Music Integration**
   - Can AppleScript reliably handle all metadata fields we need (year, genre, BPM, key, comments)?
   - What's the safe concurrency model for batch updates (one-at-a-time, batched, transactional)?

4. **MusicBrainz/Discogs Integration**
   - Which API provides better metadata for DJ-oriented music (electronic, house, techno)?
   - How to handle API rate limits for large batch operations?

5. **Performance Target**
   - What's the acceptable optimization time for a 30-song playlist? (Current: ~30 min, Python optimized: ~10 min?, Rust: <3 min?)
   - Is Rust port worth the effort if Python can achieve 10-minute runtime?

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
- **Safety First**: Read-only XML approach until AppleScript is thoroughly tested
- **Performance**: Python mixer works but is slow; Rust is future optimization, not immediate blocker
- **Backup**: Always backup Apple Music library before any batch metadata operations
