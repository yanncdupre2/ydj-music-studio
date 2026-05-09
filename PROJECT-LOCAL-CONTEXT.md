# Project Specific Context

## Purpose
Comprehensive DJ music production and library management system for YDJ, encompassing playlist optimization (harmonic mixing), Apple Music library metadata management, and YouTube media processing.

**Karaoke video processing pipeline (v2 feature-complete + GUI, awaiting v1 promotion)**: `karaoke-processing/karaoke-process-v2` adds these options on top of the v1 luminance-LUT pipeline: independent intro/outro segments via `--intro-preserve N` / `--intro-blackout N` / `--outro-preserve N` / `--outro-blackout N` (each side can preserve the segment unaltered or replace it with a fully black frame; pairs mutually exclusive; intro+outro must sum < duration); `-z PERCENT` (uniform centered zoom); `--invert-bands` (swap mid/high LUT bands — rescues Party Tyme/APT-style channels); `--outline N` (high-contrast two-ring gray halo, default 2); `-o OUTPUT_DIR` (redirect outputs); `--sung-color HEX` (customizable sung-text color, default `00C800`); and `--bg-color HEX` + `--bg-strength` / `--bg-range` / `--bg-blend` (optional background darken for Karafun-style colored backgrounds). Pipeline insertion order in body: `mask → bg-darken → zoom → grayscale → LUT → outline`; intro/outro branches stay untouched. The filter chain is a 3-way concat `[intro][body][outro]` (or 2-way / no-concat depending on which sides are active). A SwiftUI macOS app `karaoke-processing/karaoke-process-gui/` wraps the script with live previews, persisted presets (including bg-darken fields), white aspect-ratio borders on all image panels, and a foreground progress bar driven by parsing ffmpeg stderr. Quick Action Automator workflow at `karaoke-processing/Karaoke Process v2.workflow/` invokes the app via Finder right-click. End-to-end validated on ROSÉ & Bruno Mars - APT (no bg-darken) and Depeche Mode/Christophe/Frank Sinatra Karafun samples (with bg-darken). Next: validate v2 across more channels, then promote v2 → v1 by replacing `~/.local/bin/karaoke-process`.

## Completed Phases
- ✅ **Phase 1:** Foundation & Organization — modular structure, genres.json, Git/GitHub
- ✅ **Phase 4:** AppleScript integration — direct year/genre updates to Apple Music working

## Recent Session (2026-05-08)
- ✅ **Mask-margin-zero bug fix in `karaoke-process-v2`**: Setting any margin to 0% (via CLI or GUI slider) produced an entirely black "masked" preview/output. Root cause: ffmpeg's `drawbox` documents that `w=0` or `h=0` is interpreted as the full input dimension, so a strip with a zero side painted the whole frame black. The script previously emitted four `drawbox` calls unconditionally (top/bottom/left/right strips, or four corners with `--corners-only`); when a side was 0, the corresponding strip's width or height was 0 → full-frame fill. Fix: build `mask_filter` from non-empty strips only; if all four margins are 0, fall back to a passthrough `null` filter. Same logic applied to the `--corners-only` path. Verified with synthetic input (red 320x240): all-zero margins pass through; mixed zero/non-zero margins mask only the requested sides; defaults (5/15/15/5) unchanged.
- ✅ **CLI rename + outro support**: dropped `-splash` (v2 was still in validation, GUI is the only consumer). Added four flags: `--intro-preserve N`, `--intro-blackout N`, `--outro-preserve N`, `--outro-blackout N`. Each `*-preserve`/`*-blackout` pair errors out if both are passed (instead of silent precedence); `intro_secs + outro_secs < duration` enforced. Filter chain refactored into a generalized concat builder: each side may produce an `[intro]` or `[outro]` branch (preserve = trim only; blackout = trim + `drawbox=...:fill` covering the full frame); the body branch trim becomes `start=intro_secs:end=duration−outro_secs` with the relevant fields omitted when one side is off. Audio is still mapped from `0:a:0` and stream-copied — the rebuilt video timeline matches the original audio. Filename tokens: ` intro-keep-N` / ` intro-bo-N` / ` outro-keep-N` / ` outro-bo-N`. Validated with the matrix: preserve+preserve, blackout+blackout, mixed, intro-only, outro-only, no-flags, both error paths, duration overflow, still-frame ignore note, and the bg-darken+outline+intro+outro stack. Mask-zero fix and intro/outro feature shipped in the same commit.
- ✅ **GUI Intro/Outro UI**: replaced the single "Splash" section with parallel **Intro** and **Outro** sections in the right column. Each: enable toggle (autocaptures from playhead — Intro = `currentSeconds`, Outro = `duration − currentSeconds`), duration text field, horizontal **Preserve | Blackout** radio group. New `IntroOutroMode` enum (preserve/blackout). `cliArgs(includeIntroOutro:)` (renamed from `includeSplash:`) emits the right flag based on mode. Old `splashEnabled` / `splashSeconds` / `introBlackoutEnabled` fields removed from `ProcessingParameters`; presets always saved those defaulted to false/5/false, so old preset files decode cleanly to new defaults via `decodeIfPresent`. Preset semantics unchanged: intro/outro params are carried over (not overwritten) when applying a preset, and reset to defaults before saving.
- 📌 **GUI binary location**: `/Applications/KaraokeProcessGUI.app` updated to the intro/outro build. Old app moved to `~/.Trash/KaraokeProcessGUI.app.<timestamp>` (per global "never `rm`" preference).

## Recent Session (2026-05-07, evening)
- ✅ **Background darken feature for `karaoke-process-v2` + GUI**: Optional pre-LUT pass that pushes pixels matching a target color toward black so the LUT can quantize colored Karafun backgrounds (deep blue, olive, orange) into the low-luminance bucket. **Script:** 4 new flags — `--bg-color HEX` (activator), `--bg-strength N` (DS, 0-100, default 85), `--bg-range N` (CR, 0-100, default 35), `--bg-blend N` (default 10). Pipeline insertion: `mask → bg-darken → zoom → grayscale → LUT → outline`; splash branch unaffected. When bg-darken is active, the script always uses `filter_complex` (split/overlay needs labeled pads); when off, the existing `-vf` simple-chain path is preserved. Filename token: ` bg-RRGGBB-DSnn-CRnn-BLnn`. **GUI:** new "Background darken" section in `ParametersPanel` left column (between Margins and Zoom — matches pipeline order) with checkbox + SwiftUI `ColorPicker` (uses standard macOS color panel with built-in eyedropper for sampling video pixels) + 3 sliders. Default bg color `0040C0` (representative blue) used on first activation; subsequently it remembers last pick. Models gained 5 new fields (`bgDarkenEnabled`, `bgColor`, `bgStrength`, `bgRange`, `bgBlend`), all decoded with `decodeIfPresent ?? default` so existing presets keep working and new presets persist all 5 fields.
- 📌 **Filter design pivot mid-implementation**: Originally wired up with `hsvkey` (matches our `docs/bg-removal-tests/` validation scripts), but discovered during CLI integration testing that `hsvkey` is broken in ffmpeg 8.1 — even when the input pixel exactly matched the target hue/sat/val, the alpha output stayed at 255. Confirmed by direct testing on a pure-blue PNG: `hsvkey hue=242 sat=0.64 val=0.72 similarity=0.10` produced mean alpha 255 (no keying); `colorkey color=0x4742B8 similarity=0.10` produced mean alpha 0 (full key). Switched to `colorkey` (RGB-distance based). Re-validated bg-darken end-to-end on Depeche Mode video at frame 120s with `--bg-color 4742B8 --bg-strength 95 --bg-range 35` — bg goes pure black, lyrics render cleanly through the LUT. **CR slider mapping:** `colorkey`'s useful similarity range on Karafun frames is 0.05-0.20 (text edges start eating around 0.20). Mapped CR (0-100%) → similarity (0.01-0.30) linearly so the user's earlier intuition ("35% works") still gives a sensible result (~0.11) and the full slider range stays meaningful.
- 📌 **Backstory — earlier "successful" hsvkey tests were a mirage**: Across a long sequence of `docs/bg-removal-tests/` sweeps we'd locked in DM=CR35/DS95, C=CR45/DS95 etc. with hsvkey and saw what looked like darkening in the inline previews. Post-mortem: hsvkey at sim≈0.35 keys ~3% of pixels (alpha mean ~252 of 255) on a pure-blue input, so the dim layer barely showed through. The visual difference between settings was real but tiny; we ascribed more to it than was there. The colorkey switch revealed the actual full-strength behavior. Validation images confirming the new chain are in `docs/v2-cli-tests/`.
- ✅ **Documentation updates**: `karaoke-process.md` gained a `--bg-color` section under the v2 prototype docs; "Output Naming" section updated with a bg-darken filename example.
- 📌 **Test artifact location**: bg-darken FFmpeg validation lives in `docs/bg-removal-tests/` (12 final PNGs from `run_ds_sweep.sh` plus 6 `DS95_CR{35,45}` follow-ups, all gitignored — local working set only). Script-level CLI tests in `docs/v2-cli-tests/` (still-frame and splash-mode encodes for DM/C). Both folders untracked; nothing committed in `docs/`.
- 📌 **GUI binary location**: `/Applications/KaraokeProcessGUI.app` updated to the bg-darken build. Old app moved to `~/.Trash/KaraokeProcessGUI-pre-bgdarken-<timestamp>.app` (per global "never `rm`" preference).

## Recent Session (2026-05-07)
- ✅ **GUI splash auto-capture bug fix**: When user toggled "Preserve intro splash" with the playhead at e.g. 5 s, the captured splash duration was a stale fraction (e.g. 0.5 s) instead of 5.00 s. Root cause: `ContentView` held `AVPlayerWrapper` as plain `@State`, so updates to `@Published var currentSeconds` did NOT trigger `ContentView` re-renders; the snapshot `currentPlayheadSeconds: player.currentSeconds` passed into `ParametersPanel` was therefore captured at some earlier render and never refreshed. The Refresh-Previews button was unaffected because its action reads `player.currentSeconds` directly inside the closure. **Fix:** `ParametersPanel` now takes `player: AVPlayerWrapper` as `@ObservedObject` (replacing the two `Double` snapshot params), and reads `player.currentSeconds` / `player.durationSeconds` live in the splash-toggle `onChange` and the bottom `t = ...` readout. The bottom readout had the same staleness issue and is now also live.
- ✅ **Delete preset**: New destructive item in the Preset dropdown menu — `Delete preset "{name}"…` — appears only when `currentPreset == .named(name)`. Since any parameter edit flips `currentPreset` back to `.custom` (via `userTouchedParameters`), this condition is equivalent to "a preset is currently selected and unmodified", which is what the user requested. Implementation: `PresetStore.delete(name:)` removes from the in-memory dict + persists; `PresetDeleteDialog.runConfirmation(name:)` is an `NSAlert` with Delete/Cancel buttons (warning style). On confirm, preset is deleted, `currentPreset` flips to `.custom`, and current parameters stay put. Built-in presets (Sing King, Musisi) ARE deletable — they only seed on first launch (when `presets.json` is absent), so deleting them is permanent unless the user removes the JSON file. User accepted this tradeoff implicitly by not flagging built-ins as protected.
- 📌 **Verified**: rebuilt via `./build.sh`, sent old `/Applications/KaraokeProcessGUI.app` to Trash (`KaraokeProcessGUI-pre-deletefix-*.app`), installed new build. User confirmed both fixes working end-to-end.

## Recent Session (2026-05-03)
- ✅ **SwiftUI app `karaoke-process-gui`**: macOS app wrapping `karaoke-process-v2` with three image panels (AVPlayer-based player, mask+zoom preview, LUT+outline preview), each with white aspect-ratio borders that trace the actual video edges (not panel chrome). Two-column parameter sidebar — Margins+Zoom on the left, Thresholds+Outline+Splash+Preset on the right — plus a wide bottom Refresh Previews bar with playhead-time readout. SPM executable target → `KaraokeProcessGUI.app` via `build.sh` (ad-hoc codesigned). Uses `NSViewRepresentable` around `AVPlayerView` (NOT SwiftUI's `VideoPlayer`, which crashed at startup on macOS 26 with `getSuperclassMetadata` in `_AVKit_SwiftUI`).
- ✅ **Foreground progress bar**: `ProcessService` runs ffmpeg as a foreground child with stderr streaming. Parses `time=HH:MM:SS.ss` lines vs. asset duration loaded from `AVURLAsset.load(.duration)`. ETA computed from elapsed wall time and progress fraction. Cancel button kills the child cleanly; closing the window also cancels. Result is a proper "Done — Reveal in Finder" / "Failed — last 1.2KB of stderr" terminal state.
- ✅ **Persisted presets**: `PresetStore` writes JSON to `~/Library/Application Support/KaraokeProcessGUI/presets.json` (pretty-printed, sorted-keys for diff-friendliness). Seeded with `Sing King` and `Musisi` on first launch. Backward-compatible decoder (`decodeIfPresent ?? default` per field) so future schema additions don't lose existing user presets. **Splash params are intentionally NOT included in saved presets** — splash is per-file, captured from playhead. "Save current as preset…" runs an `NSAlert` with text input; if the name exists, a second `NSAlert` confirms overwrite. Menu (not Picker) for the dropdown so the save action lives alongside preset names.
- ✅ **Color picker for sung text**: SwiftUI `ColorPicker` (under the hood: `NSColorPanel`) with the small swatch sitting next to the Invert bands toggle to save vertical space. App sets the shared color panel's mode to `.crayon` at launch (user can switch via the panel toolbar; macOS remembers afterward). Saved as 6-digit hex in `ProcessingParameters.sungColor`.
- ✅ **Splash auto-capture**: toggling "Preserve intro splash" ON snaps the duration field to the current video playhead time; user can edit the seconds field afterward. Old "Set splash to playhead" button removed. Splash duration is a `TextField` (no slider) — accepts decimals, comma → dot.
- ✅ **`karaoke-process-v2` flag additions**:
  - `-o OUTPUT_DIR` — redirects output PNGs/MP4 to specified dir (created if needed). Used by the GUI for per-launch tmpdir at `$TMPDIR/KaraokeProcessGUI-<pid>/`.
  - `--sung-color HEX` — customize sung-text color (the band currently rendered as green). Default `00C800` (preserves legacy filename format). Hex normalization: strip leading `#`, uppercase, validate `^[0-9A-F]{6}$`. Filename gains `-sungXXXXXX` token only when non-default; default green is filename-stable for backward compat with existing workflows.
- ✅ **v2 splash SAR fix**: explicit `setsar=1` on both concat branches in splash mode. Surfaced when running v2 from the GUI on the user's Music/Karaoke copy of APT (SAR `19520:19521`) with zoom enabled — zoom's `crop` filter normalized body SAR to 1:1, splash branch kept original SAR, concat refused. Fix is backward-compatible (already-1:1 sources are unchanged).
- ✅ **Quick Action wrapper**: `karaoke-processing/Karaoke Process v2.workflow/` — single Run-Shell-Script action `for f in "$@"; do open -a /Applications/KaraokeProcessGUI.app "$f"; done`. Restricted to movie file types (`com.apple.Automator.fileSystemObject.movie`). Drop into `~/Library/Services/`, then right-click any video → Quick Actions → "Karaoke Process v2".
- 📌 **Crash report access**: user granted read access to `~/Library/Logs/DiagnosticReports/` in `~/.claude/settings.json`. Project also has `crash-reports/` (gitignored) for preserved copies.
- 📌 **gitignore additions**: `.build/`, `*.app/`, `DerivedData/` (Swift toolchain artifacts), `crash-reports/`, `*.ips`.

## Recent Session (2026-05-02)
- ✅ **`karaoke-process-v2` prototype**: parallel script alongside the original `karaoke-process` (kept untouched). All v1 functionality preserved.
- ✅ **`-splash SECONDS`**: single-pass `concat` filter inside `filter_complex` — splash branch trims `[0:v]` to `[0,N)`, body branch trims `[N,end]` and runs the mask+LUT chain, then both concat. Audio is stream-copied (`-c:a copy -map 0:a:0`) so it's bit-perfect, no AAC frame-boundary issues. Accepts decimals. Verified on ROSÉ & Bruno Mars - APT (5s splash → splash-5; also tested at 4.5s).
- ✅ **`-z PERCENT`**: `scale=iw*z:ih*z, crop=W:H` after the mask, before the grayscale+LUT. Output dims unchanged. Verified that filter ordering matters — running the LUT *after* the scale keeps the output deterministic (3 colors), running it before would produce gray/dark-green pixels at scaled text edges.
- ✅ **`--invert-bands`**: swaps mid/high outputs in the LUT — `< lo → black`, `lo ≤ val < hi → green`, `≥ hi → white`. Rescues Party Tyme-style channels. Filename token changes from `bwg-LO-HI` to `bgw-LO-HI`. Validated on APT (`-lo 40 -hi 200 --invert-bands`): orange sung renders green, white unsung renders white.
- ✅ **`-splash` × `-f` interaction**: in still-frame mode, `-splash` is ignored with a notice (still-frame is for tuning, not segment-aware).
- ✅ **`--outline N` integrated** (default 2; 0 disables): stacked-offset gray copies for a neon-style two-ring halo. Inner stamps at ±N (gray 80), outer stamps at ±2N (gray 220), 8 compass directions, alpha-composited so the colored text core is preserved. Filter-chain slot: after LUT, before encode. Splash branch stays unaltered (outline lives only in body branch). When N=0, outline chain is skipped and the script falls back to the simpler `-vf` path. End-to-end validated on APT (full re-encode with `--outline 2 -splash 4.5 -z 10 --invert-bands --corners-only -t 0% -r 0% -b 30% -l 15%`): duration matches original, audio bit-perfect, splash untouched, body has visible 4px halo. Performance: ~3-4x slower than no-outline due to 16 overlay stamps per frame.
- ✅ **APT (Party Tyme) added as channel reference** in `karaoke-process.md`. Old "do not run" guidance for Party Tyme replaced with `--invert-bands` recipe.
- ✅ **Working folder relocated**: ~2GB karaoke-production assets moved into `docs/karaoke-production/`. `*.mp4` was already gitignored, so videos won't sync.
- 📌 **Test artifacts**: outline experiment PNGs and APT v2 test outputs live directly under `docs/` (per project convention "save test images/videos under docs, not /tmp").

## Recent Session (2026-04-29)
- ✅ **Karaoke filename support** in `downloads/rename_youtube.py`:
  - Karaoke files now get `[Karaoke]` (square brackets) instead of `(Karaoke)` (parens) — visually distinguishes karaoke from video files
  - `BAD_CHARS_RE` updated to preserve brackets (was stripping them); `OUR_OUTPUT_TAGS` regex now matches any combination of `(Video)`, `(Lyrics Video)`, `[Karaoke]`, and `(N)` index suffixes
  - Aggressive karaoke-noise stripping: 7 patterns + branded channel list (KaraFun, Zoom Karaoke, Sing King, Musisi, Party Tyme) handle fullwidth brackets `【】`, embedded pipes, trailing dash segments, "Karaoke Version from..." suffixes
  - Fullwidth char mappings added: `\u3010` `\u3011` `\u29f8` etc.
  - Tested on 16 newly-downloaded karaoke files — all renamed cleanly
- ✅ **Live Apple Music artist fetch** (replaces stale CSV dependency):
  - New helper `get_all_artists_from_app()` in `common/apple_music.py` — bulk AppleScript property fetch with `---SEP---` separator, ~5s for 3,770 artists
  - `rename_youtube.py` now calls this directly; `import pandas` removed
  - Excludes "Various Artists" entries; canonicalizes case via longest-name preference per normalized key
  - **Why:** user had not exported XML in months — CSV (Feb 13) was 2.5 months stale, missed all newly-added artists
  - Legacy CSVs (`data/cleaned_music_library.csv`, `data/your_music_library.csv`) flagged for deletion (no remaining consumers)
- ✅ **Tagging run on 37 newly-added tracks** via `/fill-missing-genres-years`:
  - Research script (Source A duplicates + Source D MusicBrainz) wrote `/tmp/recommendations.json`
  - Filled Source B (LLM knowledge) + Source C (web search) for all 37 tracks
  - **Genre-mapper gotcha discovered:** `"new wave"` (no hyphen) does NOT match `"New-Wave"` canonical (with hyphen) via substring scoring — for synth-pop/new-wave tracks, use `"synth-pop"` as the source tag instead. Similarly `"dance"` maps to bare `"Dance"` not the compound `"Dance, Disco, R&B, Soul, Funk"`; use `"disco"` instead.
  - Final consensus: **10 high / 24 medium / 3 low** confidence (improved from 6/21/10 after fixing tag choices)
  - Interactive tagger launched in new Terminal window for keypress-based confirmation

## Recent Session (2026-04-28)
- ✅ **Karaoke processing breakthrough** — replaced slow `geq` color-swap pipeline with luminance-LUT approach
  - New batch tool: `karaoke-processing/karaoke-process` (bash + ffmpeg), installed at `~/.local/bin/karaoke-process` (on PATH, callable from anywhere)
  - Approach: convert to grayscale (`hue=s=0`), then `lutrgb` maps luminance bands to fixed colors:
    - `val < lo` → black `(0,0,0)`
    - `lo ≤ val < hi` → white `(255,255,255)`
    - `val ≥ hi` → green `(0,200,0)`
  - Defaults: `-lo 40 -hi 80`, edge masks `-t 5% -b 15% -l 15% -r 5%`
  - Edge masking via `drawbox` (full strips by default, or `--corners-only` for just the implied corners)
  - **Still-frame mode** (`-f SECONDS`): emits a masked-only PNG and a fully-processed PNG at that timestamp — used to tune `-lo`/`-hi` thresholds and mask geometry without re-encoding the whole video
  - Output naming encodes parameters: `[outer box-T-B-L-R bwg-LO-HI].mp4` for video, `[frame-N processed-... bwg-LO-HI].png` for stills
  - Full-video mode: re-encodes video (libx264, yuv420p, crf 18), copies audio, strips chapters/data tracks
  - Performance: near realtime on 1080p (vs `geq` at ~0.1x); a 4-minute song now processes in minutes, not 40 min
  - Goal/rationale and channel-specific findings (Musisi/Sing King/Party Tyme starting points, tuning workflow) lifted into `karaoke-process.md`; the old `geq`-based design doc was moved to Trash since the technical pipeline is fully superseded
- ✅ **yt-dlp setup**: Configured `~/.config/yt-dlp/config` for YouTube downloading
  - h264 codec (not AV1 — macOS Quick Look incompatible), 1080p max, Safari cookies for YouTube Premium
  - No metadata embedding, no thumbnails (Apple Music tags set manually)
  - Downloads to `~/Movies/YouTube Downloads/`
- ✅ **YouTube rename script** (`downloads/rename_youtube.py`):
  - Reads artist list **live** from Apple Music via AppleScript (`get_all_artists_from_app()` in `common/apple_music.py`) — no CSV/XML dependency, ~5s for ~3,700 artists
  - Karaoke files use `[Karaoke]` (square brackets); video files use `(Video)` / `(Lyrics Video)` (parens)
  - Aggressive karaoke-noise stripping when filename contains "karaoke" anywhere (handles KaraFun, Zoom Karaoke, fullwidth brackets `【】`, embedded pipes, etc.)
  - Normalizes to `Artist - Title (Video/Karaoke/Lyrics Video).mp4` format
  - Handles: feat. normalization, fullwidth Unicode, @handles, karaoke prefix, noise tags
  - Idempotent (skips already well-formed files), duplicate-safe (adds index suffix)
  - Dry-run by default, `--apply` to rename

## Recent Session (2026-02-18)
- ✅ **Bridge candidate smart playlists**: 24 key-filter playlists + 24 Candidates playlists created in Apple Music
  - Key-filter naming convention confirmed: `XA or Y(+1) or Z(-1)` where Y/Z are the base keys that reach XA via ±1 semitone shift
  - Example: `6A or 11A(+1) or 1A(-1)` (not `6A(-1)` — the sign indicates the shift applied to the base key)
  - Candidates playlists filter: IN key-filter playlist AND IN "DJ All" AND NOT IN "Mixer input"
  - 22 key-filter playlists created manually; 21 Candidates playlists renamed via AppleScript (`osascript`)
  - `mixer/create_key_playlists.py` written but unused (Apple Music `duplicate` creates regular playlists, not smart ones)
- ✅ **AppleScript rename capability confirmed**: can rename any playlist (smart or regular) via `first playlist whose name is "..."` + `set name`

## Recent Session (2026-02-17, late night)
- ✅ **Held-Karp exact optimizer implemented** (`src/ydj_mixer_engine/src/held_karp.rs`)
- ✅ DP on bitmask subsets: state (mask, last_track, shift_idx), O(n²·2ⁿ·9)
- ✅ Backtracking without parent table (searches DP table; all costs are exact half-integers)
- ✅ `optimize_mix_exact()` exported via PyO3 in `lib.rs`
- ✅ `mixer.py` dispatch: n ≤ 20 → HK exact; n > 20 → SA; no Rust → Python SA
- ✅ `USE_RUST_EXACT` flag; `HELD_KARP_MAX_TRACKS = 20` constant
- ✅ Verified against brute-force: 20 random tests (n=4–6), all match exactly
- ✅ **Performance: n=17 in 0.43s, n=20 in 4.2s** (global optimum, no time budget needed)
- ✅ **Improved mix output**: bridge hints now appear as `>> ` rows between tracks
  - Both harmonic bridges (h_cost ≥ 5) and tempo bridges (t_cost > 0) shown
  - BPM range = intersection of both neighbors' ±4 BPM windows (correct bridge target)
  - Keys expanded to all ±1 semitone variants (12 keys for 4 effective keys, no spaces around /)
  - Format: `>> [label] - keys: K1/K2(+1)/K3(-1)/... - BPM xxx`
- ✅ `run-mixer.sh`: added `source "$HOME/.cargo/env"` so Rust engine loads correctly
- ✅ `HELD-KARP-PLAN.md` status updated to COMPLETE
- ✅ `OPTIMIZER-PLAN.md` updated with Phase C entry
- **Build command**: `cd src/ydj_mixer_engine && maturin develop --release`

## Recent Session (2026-02-17, night)
- ✅ **Phase 5: Rust SA engine implemented** (`src/ydj_mixer_engine/`)
- ✅ Rust 1.93.1 + maturin 1.12.2 installed; crate built with PyO3 + rand
- ✅ `optimize_mix()` in Rust: full timed outer loop, delta cost, escape mode, shift optimization
- ✅ Python fallback: `USE_RUST = False` if `ydj_mixer_engine` not importable
- ✅ **Measured speedup: 60x** (Python 0.2 att/s → Rust 12.0 att/s, 17 tracks)
- ✅ Rust finds better solutions (40.5 vs 44.5 best cost in 10s) due to 40x more attempts
- ✅ `.gitignore` updated (Rust `target/`), `requirements.txt` updated (maturin)
- ✅ `OPTIMIZER-PLAN.md` updated with Phase B status and measured results
- **Build command**: `cd src/ydj_mixer_engine && maturin develop --release`

## Recent Session (2026-02-17, evening)
- ✅ DOE for SA annealing parameters completed: 9 variations (init temp 300/500/700 × final temp 0.05/0.1/0.15), 879 total attempts
- ✅ **DOE conclusion**: nominal values (500 → 0.1, 410k iterations) confirmed optimal — no variation statistically better
- ✅ **Key insight**: solution quality is driven by random initial arrangement, not temperature schedule (Pearson r = -0.135)
- ✅ Time budget increased from 3 to 5 minutes (~80 attempts for 17 tracks)
- ✅ DOE results saved to `mixer/doe_temperature_results.csv` (879 rows)
- ✅ `DOE-ANNEALING-PARAMS.md` updated with full findings

## Previous Session (2026-02-17, morning)
- ✅ Mixer reads from "Mixer input" Apple Music playlist via AppleScript (no hardcoded track list or XML)
- ✅ Added BPM, Comments, Rating fields to `load_playlist_from_app()`
- ✅ Added `load_dj_playlists_from_app()` for candidate library (disabled for now)
- ✅ Time-budgeted optimizer: runs attempts until time limit instead of fixed count
- ✅ Bridge key suggestions for high-cost transitions (shows what keys to look for)
- ✅ 3x penalty for unreachable harmonic transitions
- ✅ SA performance optimization: delta cost (O(1) vs O(n)), integer key IDs, flat cost arrays → 2.8x speedup
- ✅ Created OPTIMIZER-PLAN.md (Python + Rust optimization roadmap)
- ✅ Created DOE-ANNEALING-PARAMS.md (experiment plan for tuning SA parameters)

## Previous Session (2026-02-16)
- ✅ Added locked fields: consistent metadata preserved, only inconsistent fields resolved
- ✅ Added targeted web search (Source C) for year-only inconsistency groups
- ✅ Resolver displays locked fields with "(locked)" indicator

## Previous Session (2026-02-15)
- ✅ Fixed AppleScript track update reliability with artist+name search fallback
- ✅ Eliminated dependency on fresh XML exports for track updates

## Previous Session (2026-02-14)
- ✅ Built interactive inconsistency resolver (detect → research → fix/ignore per group)
- ✅ Added `add_tracks_to_playlist()` AppleScript capability
- ✅ Created `/resolve-inconsistencies` slash command (229 groups detected in 8,549 DJ tracks)

## Constraints and Conventions

### Safety Constraints
- **AppleScript writes are live**: Year and genre updates go directly to Apple Music via AppleScript
- **Always backup before bulk operations**: Apple Music library contains 10,000+ tracks
- **Interactive confirmation**: Tagger requires manual keypress (1/2/S) per track — no unattended bulk writes

### Genre Taxonomy Rules
- Use compound genres exactly as they appear in library (e.g., "EDM, House, Techno")
- 31 canonical genres cover tracks with 20+ songs
- Smaller genres (<20 songs) will be reclassified later
- Compound genres solve "is it House or Techno?" ambiguity problem

### Code Conventions
- Python 3.x for all automation scripts
- Bash/shell scripts for media processing (ffmpeg-based)
- Each subfolder has its own `CLAUDE.md` for focused AI agent context
- Shared utilities go in `common/` folder

### File Naming
- Use kebab-case for folders: `library-management`, `ydj-music-studio`
- Python modules: snake_case (e.g., `apple_music.py`, `metadata_utils.py`)
- Shell scripts: snake_case with `.sh` extension

## Architecture / Key Paths

### Project Structure
```
ydj-music-studio/
├── PLANNING.md                    # Vision, strategy, phases (why/what/when)
├── PROJECT-LOCAL-CONTEXT.md       # This file (how/where/with what)
├── CLAUDE.md                      # Static stub → reads PLANNING + this + global
├── AGENTS.md                      # Static stub (identical to CLAUDE.md)
├── GEMINI.md                      # Static stub (identical to CLAUDE.md)
├── README.md                      # User-facing overview
├── requirements.txt               # Python dependencies
├── .gitignore                     # Exclude venv, data, media
│
├── common/                        # Shared utilities across subprojects
│   ├── apple_music.py             # XML reader (future: AppleScript integration)
│   ├── metadata_utils.py          # Common metadata operations
│   ├── genres.json                # Canonical 31-genre taxonomy
│   └── README.md
│
├── mixer/                         # Playlist optimization engine
│   ├── CLAUDE.md                  # Mixer-specific AI context
│   ├── mixer.py                   # Simulated annealing optimizer
│   ├── camelot.py                 # Camelot wheel system
│   ├── playlist_manager.py        # Dynamic playlist management (TBD)
│   └── README.md
│
├── library-management/            # Tagging, cleanup, organization
│   ├── CLAUDE.md                  # Library mgmt AI context
│   ├── cleanup.py                 # Discrepancy finder and resolver
│   ├── rename_files.py            # File renamer based on metadata
│   ├── tag_updater.py             # Batch tag updates (TBD)
│   └── README.md
│
├── downloads/                     # YouTube download processing
│   ├── CLAUDE.md                  # Download processing AI context
│   ├── rename_youtube.py          # Rename YouTube downloads (Artist - Title format)
│   ├── process_mkv.sh             # Video classification (real vs static image)
│   ├── convert_mkv_to_mp4.sh      # Lossless remuxing
│   ├── reencode_mkv_to_mp4.sh     # Transcoding for incompatible codecs
│   ├── reencode_all_mkv.sh        # Batch transcoding
│   ├── convert_opus_to_aac.sh     # Opus→AAC audio conversion
│   └── README.md
│
├── data/                          # Working data files
│   └── exports/                   # Apple Music XML exports (gitignored, optional)
│
├── venv/                          # Python virtual environment (gitignored)
├── karaoke-processing/            # Karaoke video processing batch tool
│   ├── karaoke-process            # Bash + ffmpeg script (installed at ~/.local/bin/karaoke-process)
│   └── karaoke-process.md         # Authoritative reference: goal/rationale, usage, options, channel-specific starting points, tuning workflow
└── src/
    └── ydj_mixer_engine/          # Rust SA engine (Phase 5)
        ├── Cargo.toml             # pyo3 + rand deps
        ├── pyproject.toml         # maturin build config
        └── src/
            ├── lib.rs             # PyO3 module, optimize_mix() entry point
            ├── annealing.rs       # SA loop: timed outer loop, delta cost, escape mode
            └── cost.rs            # Edge cost on flat integer arrays, shift optimizer
```

### Key Files
- `library-management/research_tracks.py` - 4-source metadata research (duplicates, LLM, web, MusicBrainz)
- `library-management/tag_tracks.py` - Interactive single-keypress batch tagger (AppleScript writes)
- `library-management/resolve_inconsistencies.py` - Phase 1: detect inconsistency groups + MusicBrainz research
- `library-management/resolve_tagger.py` - Phase 2: interactive resolver (Fix/Ignore/Skip per group)
- `library-management/sources/genre_mapper.py` - Genre mapping and consensus logic
- `library-management/sources/duplicates.py` - Source A: duplicate-based metadata inference
- `library-management/sources/musicbrainz.py` - Source D: MusicBrainz API queries
- `run-tagger.sh` - Wrapper to run tag_tracks.py from project root
- `run-resolver.sh` - Wrapper to run resolve_tagger.py from project root
- `mixer/create_key_playlists.py` - One-time utility: duplicates a template playlist and renames copies (used for Candidates playlists via AppleScript rename)
- `mixer/mixer.py` - SA optimizer: Rust engine (USE_RUST) with Python fallback; reads "Mixer input" playlist
- `mixer/OPTIMIZER-PLAN.md` - Python + Rust optimization roadmap (Phase B complete)
- `mixer/DOE-ANNEALING-PARAMS.md` - SA parameter DOE results (nominal values confirmed optimal)
- `src/ydj_mixer_engine/src/lib.rs` - PyO3 entry point: `optimize_mix()` and `optimize_mix_exact()` exported to Python
- `src/ydj_mixer_engine/src/annealing.rs` - Rust SA loop: timed multi-attempt, delta cost, escape mode
- `src/ydj_mixer_engine/src/cost.rs` - Edge cost, shift optimizer on flat integer arrays
- `src/ydj_mixer_engine/src/held_karp.rs` - Held-Karp DP exact optimizer (n ≤ 20)
- `common/apple_music.py` - XML reader + AppleScript playlist management (BPM/Comments/Rating fields)
- `common/genres.json` - Canonical 31-genre taxonomy
- `downloads/rename_youtube.py` - YouTube download renamer (uses Apple Music artist list for disambiguation)
- `karaoke-processing/karaoke-process` - Bash batch tool for karaoke video prep (luminance-LUT pipeline; mirrored to `~/.local/bin/karaoke-process`)
- `karaoke-processing/karaoke-process-v2` - Bash + ffmpeg script with full feature set: `--intro-preserve` / `--intro-blackout` / `--outro-preserve` / `--outro-blackout` (independent intro/outro segment handling, mutually exclusive within each side; concat builder produces 0/2/3-way concat depending on what's active), `-z`, `--invert-bands`, `--outline N`, `-o OUTPUT_DIR`, `--sung-color HEX`, `--bg-color HEX` + `--bg-strength` / `--bg-range` / `--bg-blend` (background darken via `colorkey`). Will replace v1 once validated across all channels.
- `karaoke-processing/karaoke-process.md` - Authoritative reference: goal/rationale, options, defaults, still-frame mode, output naming, channel-specific starting points (Musisi/Sing King/Party Tyme/APT), v2 prototype section, GUI app section, tuning workflow
- `karaoke-processing/karaoke-process-gui/` - SwiftUI macOS app source. SPM executable target. Build via `./build.sh` → `KaraokeProcessGUI.app` (ad-hoc codesigned). Sources: `App.swift` (entry + AppDelegate + AppState singleton + script discovery), `ContentView.swift` (top-row split + bottom-row split + status row), `ParametersPanel.swift` (2-col params + bottom Refresh bar + ColorPickers for sung-color and bg-color + Background darken section + Intro section + Outro section, each with Preserve|Blackout radio group; observes `AVPlayerWrapper` directly so playhead reads are always live), `VideoPanel.swift` (NSViewRepresentable around AVPlayerView + AVPlayerWrapper with currentSeconds/durationSeconds/videoAspectRatio), `PreviewPanel.swift` (NSImage display with optional aspect-ratio white border), `Models.swift` (ProcessingParameters + Codable + CurrentPreset enum + IntroOutroMode enum; bg-darken + intro/outro fields included), `Presets.swift` (PresetStore JSON persistence + save/delete + PresetSaveDialog + PresetDeleteDialog NSAlert flows; bg-darken fields persist; intro/outro fields excluded from saved presets), `PreviewService.swift` (shells `karaoke-process-v2 -f -o cacheDir`, parses Created: paths from stdout, returns NSImages), `ProcessService.swift` (foreground Process with stderr streaming, `time=` regex parsing for progress bar, terminationHandler for cleanup).
- `karaoke-processing/Karaoke Process v2.workflow/` - Automator Quick Action: single Run-Shell-Script action that calls `open -a /Applications/KaraokeProcessGUI.app "$f"` for each selected movie. Restricted to movie file types. Install: `cp -R "Karaoke Process v2.workflow" ~/Library/Services/`.
- `karaoke-processing/PROCESS PARTY TYME.workflow/` - Legacy reference workflow encoding the blue-background chromakey trick (drawbox blue cover + `colorkey=0x130FE6` over black). Will inform a future `--bg-chromakey` flag for v2.
- `karaoke-processing/Replace Lower Left Corner w BK (Sing King).workflow/` and `Replace Lower Right Corner w BK (Sing King).workflow/` - Legacy reference workflows for Sing King logo masking (now superseded by v2's `--corners-only` + margin tuning).
- `~/Library/Application Support/KaraokeProcessGUI/presets.json` - User-saved processing presets (pretty-printed JSON, sorted-keys). Seeded with Sing King + Musisi on first launch; user owns it after that.
- `~/.local/bin/karaoke-process` - Installed copy of v1 (PATH-accessible from anywhere); v2 is run from the project tree until promoted
- `/Applications/KaraokeProcessGUI.app` - Installed GUI app; rebuild from `karaoke-processing/karaoke-process-gui/` and replace.
- `~/.config/yt-dlp/config` - yt-dlp configuration (h264/1080p, no metadata, Safari cookies)

## Run Commands / Environment

### Python Environment Setup
```bash
cd ~/Projects/ydj-music-studio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Required Python Packages (requirements.txt)
- pandas
- numpy
- mutagen (audio file metadata)
- fuzzywuzzy (fuzzy string matching)
- python-Levenshtein (fuzzywuzzy speedup)

### Apple Music Integration
**Reading:** Smart playlists read directly via AppleScript (e.g., "Genre or Year Blank")
**Writing:** Year and genre updated via AppleScript (`tag_tracks.py`)
  - Primary: Artist+name search (reliable, no XML dependency)
  - Fallback: Database ID (legacy compatibility)
**XML Export:** Used for bulk metadata reading (`~/YDJ Library.xml`)

### YouTube Downloading (yt-dlp)
```bash
# Download a video or playlist
yt-dlp "https://www.youtube.com/watch?v=...&list=PL..."
# Config at ~/.config/yt-dlp/config: h264, 1080p, Safari cookies, no metadata/thumbnails
# Downloads to ~/Movies/YouTube Downloads/

# Rename downloaded files to consistent format
python3 downloads/rename_youtube.py          # dry-run
python3 downloads/rename_youtube.py --apply  # actually rename
```

### Media Processing (ffmpeg)
```bash
# Install ffmpeg via Homebrew (if not already installed)
brew install ffmpeg

# Process MKV files in downloads folder
cd ~/Projects/ydj-music-studio/downloads
./process_mkv.sh           # Classify and extract audio from static videos
./convert_mkv_to_mp4.sh    # Lossless remux compatible files
./reencode_all_mkv.sh      # Transcode incompatible codecs
./convert_opus_to_aac.sh   # Convert Opus audio to AAC

# Karaoke video processing — use the karaoke-process batch tool (installed globally)
# Full reference: karaoke-processing/karaoke-process.md
karaoke-process "/path/to/video.mp4"                              # full video, defaults
karaoke-process "/path/to/video.mp4" -lo 24 -hi 80                # custom luminance thresholds
karaoke-process "/path/to/video.mp4" -t 20% -b 20% -l 20% -r 20%  # custom edge masks
karaoke-process "/path/to/video.mp4" -f 90                        # still-frame at 90s (PNG outputs for tuning)
karaoke-process "/path/to/video.mp4" -b 20% -l 20% --corners-only -f 20  # corners-only mask preview
```

### Mixer Usage (Current)
```bash
cd ~/Projects/ydj-music-studio
source venv/bin/activate
python3 mixer/mixer.py
# Reads from "Mixer input" Apple Music playlist, optimizes for 5 minutes
# Uses Rust engine (ydj_mixer_engine) if built; Python fallback otherwise
```

### Rust Engine Build (required once after clone)
```bash
# Install Rust (one-time)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
# Build the extension into the venv
cd ~/Projects/ydj-music-studio
source venv/bin/activate
pip install maturin
cd src/ydj_mixer_engine && maturin develop --release
```

## Integrations / Assets

### Apple Music Library
- **Location**: `~/YDJ Library.xml` (manual XML export)
- **Format**: Apple PropertyList (plist) XML
- **Size**: ~10,000 tracks
- **Update Frequency**: Manual export as needed

### Genre Taxonomy
- **Location**: `common/genres.json`
- **Source**: Extracted from Apple Music library
- **Count**: 31 compound genres (20+ songs threshold)
- **Format**: Simple JSON array of strings

### Media Files
- **YouTube Downloads**: User's download folder (outside repo)
- **Processed Media**: Moved to `processed/` subfolder after conversion
- **Working Directory**: Downloads happen outside repo; scripts process in-place

### External APIs
- ✅ MusicBrainz: Release dates, genres (integrated in `sources/musicbrainz.py`, 1 req/sec rate limit)
- Discogs: DJ-focused metadata (future)
- Spotify: Audio features, modern genres (future)
- Last.fm: Genre tags, similar artists (future)

## Slash Commands
- `/fill-missing-genres-years` — End-to-end workflow: research → LLM/web fill → interactive tagging
- `/resolve-inconsistencies` — Detect and resolve year/genre conflicts across track variants (229 groups)
- `/rebaseline-project` — Update docs and commit to GitHub
- `/update-project-todos` — Sync Todoist

## Notes
- Smart playlist "Genre or Year Blank" drives the missing-metadata tagging workflow
- "Ignore year or genre inconsistencies" playlist filters out already-resolved groups
- Interactive scripts (`tag_tracks.py`, `resolve_tagger.py`) require a real TTY — run via `run-tagger.sh` / `run-resolver.sh`
- XML export (`~/YDJ Library.xml`) used for bulk detection; AppleScript used for reads/writes
