# YDJ Music Studio

## Status
- [x] Planning
- [x] In Progress
- [ ] On Hold
- [ ] Completed

## Project Metadata
- **Project Number:** 02
- **Folder:** `ydj-music-studio` (permanent identifier)
- **Original Name:** DJ Music Library Manager
- **Current Name:** YDJ Music Studio
- **Status:** In Progress
- **Created:** 2026-02-13
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
- Direct Apple Music library write operations (deferred to Phase 4 for safety)
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

## Strategy and Phases

### Phase 1: Foundation & Organization (Complete)
**Goal:** Establish clean modular structure and migrate existing tools

- ✅ Organize existing scripts into modular subfolder structure
- ✅ Extract canonical 31-genre taxonomy from library to `common/genres.json`
- ✅ Create shared Apple Music XML reader in `common/`
- ✅ Set up Git repository and push to GitHub
- ✅ Create fresh Python virtual environment with requirements.txt
- ✅ Move existing YDJ folder contents into organized structure

**Success Criteria:**
- ✅ Clean separation: mixer/, library-management/, downloads/, common/
- ✅ Each subfolder has focused CLAUDE.md for AI agent context
- ✅ All existing scripts functional in new structure

### Phase 2: Library Management Enhancement (In Progress)
**Goal:** Improve metadata quality and consistency across library

- ✅ LLM-powered genre auto-tagging using canonical 31-genre taxonomy (4-source consensus system)
- ✅ Batch year lookup from MusicBrainz (Source D)
- ✅ Duplicate-based metadata inference (Source A)
- ✅ Web search + LLM knowledge for gap-filling (Sources B + C)
- ✅ Interactive single-keypress tagger (`tag_tracks.py`)
- ✅ `/fill-missing-genres-years` slash command for streamlined workflow
- ✅ Interactive inconsistency resolver for track variants (`resolve_inconsistencies.py` + `resolve_tagger.py`)
- ✅ Add-to-playlist AppleScript capability (`add_tracks_to_playlist()` in `common/apple_music.py`)
- ✅ `/resolve-inconsistencies` slash command (229 groups detected across 8,549 DJ tracks)
- ✅ AppleScript artist+name search (eliminates stale XML database ID dependency)
- ✅ Locked fields: consistent metadata preserved, only inconsistent fields resolved
- ✅ Targeted web search (Source C) for year-only inconsistencies to avoid MusicBrainz reissue years
- ✅ Live AppleScript artist fetch (`get_all_artists_from_app()`) — eliminates stale CSV dependency in `rename_youtube.py`
- ✅ Karaoke filename support (`[Karaoke]` brackets) + aggressive noise stripping for branded karaoke channels
- ✅ Karaoke v2 (`karaoke-process-v2`): `-splash` (preserve intro), `-z` (zoom), `--invert-bands` (rescue Party Tyme-style channels), `--outline N` (default 2; 0 disables; high-contrast two-ring gray halo via stacked-offset gray copies, 8-compass directions, alpha-composited). End-to-end validated on ROSÉ & Bruno Mars - APT.
- ✅ Karaoke v2 splash SAR fix: explicit `setsar=1` on both concat branches; videos with non-1:1 source SAR (e.g., 19520:19521) no longer fail filter-graph init when zoom is enabled.
- ✅ Karaoke v2 `-o OUTPUT_DIR` flag — redirects output away from the source folder. Used by GUI for per-launch preview tmpdir.
- ✅ Karaoke v2 `--sung-color HEX` flag — customizable sung-text color (default `00C800`). Filename gains `-sungXXXXXX` token only when non-default; default green is filename-stable for backward compat.
- ✅ **Karaoke GUI** (`karaoke-process-gui/`): SwiftUI macOS app wrapping `karaoke-process-v2`. Three image panels with white aspect-ratio borders (video player, mask+zoom preview, LUT+outline preview); two-column parameter sidebar (margins+zoom on left, thresholds+outline+splash+preset on right) with bottom Refresh bar. Persisted presets at `~/Library/Application Support/KaraokeProcessGUI/presets.json` seeded with Sing King + Musisi. Foreground ffmpeg processing with stderr-parsed progress bar and cancel. Quick Action wrapper at `Karaoke Process v2.workflow` invoked via Finder right-click. Built with SPM + ad-hoc codesigning via `build.sh`.
- ✅ **Karaoke GUI follow-ups (2026-05-07)**: (1) Splash auto-capture bug fix — `ContentView` held `AVPlayerWrapper` as plain `@State`, so playhead changes didn't propagate to `ParametersPanel` and the snapshot `currentPlayheadSeconds` was stale at toggle time (Refresh button worked because it read `player.currentSeconds` directly). Now `ParametersPanel` takes `player: AVPlayerWrapper` as `@ObservedObject` and reads live values for splash auto-capture and the bottom `t = ...` readout. (2) Delete preset — Preset dropdown now shows a destructive "Delete preset {name}…" item only when `currentPreset == .named(name)` (any edit flips to `.custom`, so by definition this means unmodified). Confirmation via `NSAlert` (Delete/Cancel); on delete, preset is removed from `PresetStore` and `currentPreset` flips to `.custom` while parameters stay put.
- ✅ **Karaoke v2 background darken (2026-05-07)**: New optional pre-LUT pass for Karafun-style channels with colored (non-black) backgrounds. Adds 4 CLI flags to `karaoke-process-v2` (`--bg-color HEX`, `--bg-strength N`, `--bg-range N`, `--bg-blend N`; defaults 85/35/10) and a corresponding "Background darken" section in the GUI's left column (checkbox + ColorPicker + 3 sliders). Pipeline insertion: `mask → bg-darken → zoom → grayscale → LUT → outline`; splash branch is unaffected. Filename token: ` bg-RRGGBB-DSnn-CRnn-BLnn` (only when active). Filter chain uses ffmpeg `colorkey` (RGB-distance) into an alpha mask composited over a luma-scaled copy — initially attempted with `hsvkey` but discovered it's broken in ffmpeg 8.1 (alpha output stays at 255 even on exact-target inputs); `colorkey` works correctly. CR slider maps non-linearly (0-100 → similarity 0.01-0.30) so the useful Karafun range (~20-60) lands across most of the slider. End-to-end validated via CLI on Depeche Mode (blue), Christophe (orange), and Frank Sinatra (olive) videos; user confirmed working in GUI. All 5 bg-darken fields persist in presets via the existing `decodeIfPresent ?? default` pattern.
- ✅ **Karaoke v2 intro/outro preserve+blackout (2026-05-08)**: (1) Bug fix in the mask filter: when any margin was set to 0%, ffmpeg's `drawbox` interpreted `w=0` or `h=0` as "use the full input dimension" and painted the whole frame black. Fixed by emitting drawbox calls only for non-zero strips; with all margins 0 the mask falls back to a passthrough `null` filter. (2) CLI rename + outro feature: dropped `-splash`, added `--intro-preserve N`, `--intro-blackout N`, `--outro-preserve N`, `--outro-blackout N`. Each pair is mutually exclusive (errors out, doesn't silently pick a winner); intro + outro must sum to less than the video duration. The filter chain is now a 3-way concat `[intro][body][outro]` (or 2-way when only one side is active, or no concat when neither is); body trim is `start=intro_secs:end=duration-outro_secs`; audio is mapped straight from `0:a:0` and stays in sync with the rebuilt video timeline. Filename tokens: ` intro-keep-N` / ` intro-bo-N` / ` outro-keep-N` / ` outro-bo-N`. (3) GUI: replaced the single "Splash" section with parallel **Intro** and **Outro** sections in the right column. Each has an enable toggle (autocaptures playhead — Intro = `currentSeconds`, Outro = `duration − currentSeconds`), a duration text field, and a horizontal **Preserve | Blackout** radio group. New `IntroOutroMode` enum; old `splashEnabled`/`splashSeconds`/`introBlackoutEnabled` fields removed from `ProcessingParameters` (existing presets always saved with splash defaulted to false, so they decode cleanly via `decodeIfPresent`).
- ✅ **Batched Apple Music playlist reader (2026-05-10)**: `load_playlist_from_music_app()` + helpers added to `common/load_from_music_app.py`. Reads any named playlist (including smart playlists) in 100-track batches via index-based AppleScript — same pattern as the full-library reader. Replaces the old `load_playlist_from_app()` in `common/apple_music.py` which iterated every track in a single AppleScript call and hung on playlists of any real size.
- ✅ **GUI Refresh Previews pipe-deadlock fix (2026-05-09)**: `PreviewService.ShellRunner.run` only drained stdout/stderr inside `terminationHandler`. macOS pipe buffers are ~64 KB; ffmpeg dumps the input file's full metadata to stderr on every invocation, and the script invokes ffmpeg twice for previews (mask PNG + processed PNG). Files with embedded Serato/MixedInKey markers (e.g., the user's Dire Straits karaoke source) produced ~38 KB of stderr per call → ~76 KB total → buffer fills → ffmpeg blocks mid-write → `terminationHandler` never fires → GUI spins forever. Reproduced with a standalone Swift test using the old pattern (hung past 30 s). **Fix:** drain both pipes incrementally via `readabilityHandler` (matching what `ProcessService` already does for the full encode path), accumulating into a small `PipeBuffers` reference type so Swift 6 sendable-capture rules stay happy. Verified with the same standalone test on the new pattern: 0.322 s, status 0, both PNGs created. Aspect ratio (4:3 vs 16:9) was a coincidence — the real trigger is metadata volume.
- 🚧 Audit library metadata quality (missing BPMs, keys)
- BPM detection and tagging for tracks missing tempo data

**Success Criteria:**
- ✅ All YDJ MASTER playlist tracks have genre and year set
- ✅ Consistent genre categorization using compound taxonomy
- ✅ Interactive cleanup workflow for resolving discrepancies (Fix/Ignore/Skip per group)
- ✅ Reliable track updates regardless of XML export freshness

### Phase 3: Mixer Improvements (In Progress)
**Goal:** Make playlist optimization more seamless and practical

- ✅ Dynamic playlist input: reads from "Mixer input" Apple Music playlist via AppleScript (no more hardcoded track list or XML)
- ✅ Added BPM, Comments, Rating fields to AppleScript playlist reader
- ✅ Time-budgeted optimizer: runs annealing attempts until time limit (default 5 min) instead of fixed attempt count
- ✅ Bridge key suggestions: for high-cost transitions, shows what keys an inserted track should have
- ✅ 3x penalty for unreachable harmonic transitions (was 2x) to minimize H=15 transitions
- ✅ Python-level SA optimization: delta cost evaluation (O(1) vs O(n) per iteration) + integer key lookups + flat cost arrays → 2.8x speedup
- ✅ DOE for annealing parameters: 9 variations (3 initial temps × 3 final temps), 879 attempts — nominal values (500 → 0.1, 410k iterations) confirmed optimal
- ✅ Held-Karp exact optimizer: guarantees global optimum for n ≤ 20 tracks (< 1s for n=17)
- ✅ Improved mix output: bridge hints appear as `>>` rows between tracks (harmonic + tempo); BPM range uses intersection of both neighbors' windows; keys expanded to all ±1 semitone variants
- ✅ Ascending-BPM presentation: optimal order is reversed when the last half averages a lower BPM than the first half. The transition cost function is symmetric and shifts are per-track, so the reversed order has identical cost — picking ascending trend is a free presentation choice.
- ✅ Per-run text export: writes `mixer/mix_YYYY-MM-DD_HH-MM-SS.txt` after each run with position, BPM, shift, original/effective Camelot keys, and `Artist - Title`. Files are timestamped (no overwrites) and gitignored.
- Export optimized playlist back to Apple Music
- Candidate library from DJ playlists (code ready, disabled)

**Success Criteria:**
- ✅ Optimize playlist directly from Apple Music playlist name
- ✅ Improve performance by 2-3x through algorithmic optimization (achieved 2.8x)
- ✅ DOE validated annealing parameters (no further tuning needed)
- ✅ Exact global optimum for playlists ≤ 20 tracks (Held-Karp)
- Export results back to Apple Music as new playlist

### Phase 4: Safe Apple Music Write Testing (Complete)
**Goal:** Enable direct library modification without risk

- ✅ Research AppleScript/JXA capabilities for Apple Music
- ✅ Implement safe write operations with validation
- ✅ AppleScript integration working for year and genre updates
- ✅ Gradual rollout to production library (used successfully on 14+ tracks)

**Success Criteria:**
- ✅ Can safely update track metadata (year, genre) via AppleScript
- ✅ Validation ensures no data corruption
- Backup/restore workflow documented and tested

### Phase 5: Rust Performance Engine (Complete)
**Goal:** 50-100x performance improvement for large playlists

- ✅ Port SA optimization loop to Rust via PyO3/maturin
- ✅ Python handles I/O (Apple Music, printing), Rust handles compute
- ✅ Precomputed integer tables passed from Python; Rust is a pure optimization engine
- ✅ Detailed plan and results in `mixer/OPTIMIZER-PLAN.md`

**Success Criteria:**
- ✅ Rust engine produces equivalent results to Python version
- ✅ 60x throughput improvement measured (0.2 → 12.0 att/s); 3,561 attempts in 5 min vs ~80 Python
- ✅ Fallback to Python SA loop when Rust module not installed
- ✅ Seamless integration: `maturin develop --release` to build, same `mixer.py` entry point

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

### Decision: Held-Karp Exact Optimizer (Phase C)
**Context:** Rust SA engine runs 3,561 attempts in 5 min but still cannot guarantee the global optimum. With 17 tracks, SA found best cost 40.5 over thousands of attempts; Held-Karp found 40.5 in 0.43s — guaranteed optimal.

**Decision:** Add Held-Karp DP optimizer in Rust alongside SA. Dispatch: n ≤ 20 → Held-Karp (exact, seconds); n > 20 → SA (probabilistic, time-budgeted).

**Rationale:**
- Held-Karp is O(n² · 2ⁿ): exponential but tractable for n ≤ 20 (< 1s for n=17, ~4s for n=20)
- Reuses the same precomputed flat integer tables as SA — zero new data structures from Python side
- SA fallback is untouched; large playlists (n > 20) continue using the 60x Rust SA engine
- For typical DJ sets (15–20 tracks), the user now gets the provably best mix instantly

**Results:** n=17 in 0.43s, n=20 in 4.2s; verified against brute-force on 20 random test cases (n=4–6); all match exactly.

**Date:** 2026-02-17

### Decision: Rust SA Engine via PyO3 (Phase 5)
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

### External APIs (Future Phases)
- MusicBrainz API (release dates, genres)
- Discogs API (vinyl/DJ metadata)
- Spotify API (audio features, genres)
- Last.fm API (genre tags, similar artists)

## Success Criteria

### Phase 1 (Foundation)
- ✅ Clean modular structure (mixer/, library-management/, downloads/, common/)
- ✅ Genre taxonomy extracted and stored in `common/genres.json`
- ✅ Git repository initialized and pushed to GitHub
- ✅ All existing scripts functional in new structure

### Phase 2 (Library Management)
- <5% of library missing critical metadata (year, genre)
- Duplicate detection identifies all track variants
- LLM genre tagging achieves 90%+ agreement with manual tagging
- Interactive cleanup workflow handles 20+ discrepancies/minute

### Phase 3 (Mixer)
- Optimize playlist from Apple Music playlist name (no hardcoding)
- Export results back to Apple Music as new playlist
- 2-3x performance improvement (10-15 minutes for 30 songs)
- Visual flow chart shows harmonic/tempo transitions

### Phase 4 (Safe Write)
- Zero data loss or corruption incidents in test library (100+ write operations)
- Backup/restore workflow tested and documented
- Production library updates validated against XML export

### Phase 5 (Rust Engine)
- ✅ 60x throughput improvement (3,561 attempts in 5 min vs ~80 Python)
- ✅ Equivalent optimization results vs. Python (verified on smoke test + live run)
- ✅ Seamless Python wrapper integration via PyO3/maturin with ImportError fallback

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
