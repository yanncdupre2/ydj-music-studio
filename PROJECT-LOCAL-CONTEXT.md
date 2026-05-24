# Project Specific Context

## Purpose
Comprehensive DJ music production and library management system for YDJ, encompassing playlist optimization (harmonic mixing), Apple Music library metadata management, and YouTube media processing.

**Karaoke video processing pipeline**: `karaoke-processing/karaoke-process` is the single canonical script (the v1 prototype was retired 2026-05-09 once the consolidated script reached feature parity). On top of the basic luminance-LUT pipeline it offers: independent intro/outro segments via `--intro-preserve N` / `--intro-blackout N` / `--outro-preserve N` / `--outro-blackout N` (each side can preserve the segment unaltered or replace it with a fully black frame; pairs mutually exclusive; intro+outro must sum < duration); `-z PERCENT` (uniform centered zoom; positive = scale up + center-crop, negative = scale down + center-pad with pure black, range -100…100); `--invert-bands` (swap mid/high LUT bands — rescues Party Tyme/APT-style channels); `--outline N` (high-contrast two-ring gray halo, default 2); `--no-lut` (skip the LUT entirely; preserve multi-color text on a black background — useful for Party Tyme duets where different singers use different font colors; uses `-lo` as a floor-to-black threshold instead of the LUT low band); `-o OUTPUT_DIR` (redirect outputs); `--sung-color HEX` (customizable sung-text color, default `00C800`); and `--bg-color HEX` + `--bg-strength` / `--bg-range` / `--bg-blend` (optional background darken for Karafun-style colored backgrounds; bg-darken's `lutyuv` step also pulls chroma toward neutral 128 so matched pixels actually go to true black even without the LUT). Pipeline insertion order in body: `mask → bg-darken → zoom → (LUT or floor-to-black) → outline`; intro/outro branches stay untouched. The filter chain is a 3-way concat `[intro][body][outro]` (or 2-way / no-concat depending on which sides are active). A SwiftUI macOS app `karaoke-processing/karaoke-process-gui/` wraps the script with live previews, persisted presets (including bg-darken and applyLut fields), white aspect-ratio borders on all image panels, and a foreground progress bar driven by parsing ffmpeg stderr. Quick Action Automator workflow at `karaoke-processing/Karaoke Process.workflow/` invokes the app via Finder right-click. End-to-end validated on ROSÉ & Bruno Mars - APT (LUT mode), Depeche Mode/Christophe/Frank Sinatra Karafun samples (LUT + bg-darken), and Britney Spears - Criminal (Party Tyme, --no-lut + bg-darken + outline + zoomout).

## Status by Area
- **Mixer:** Rust SA + Held-Karp engine shipped (60x throughput; exact for n ≤ 20); live "Mixer input" reading + timestamped mix output. Open: export back to Apple Music.
- **Library:** 4-source genre/year tagging, inconsistency resolver, and live AppleScript year+genre writes in production. Open: BPM/key audit + fill.
- **Downloads:** complete — yt-dlp rename + MKV→MP4 / Opus→AAC conversion.
- **Karaoke:** `karaoke-process` script + SwiftUI GUI mature and in use.
- **Infra:** shared `common/` utils, genre taxonomy, venv + Rust build in place. Open: Apple Music backup/restore workflow.

## Current Priority / Next Actions

*(none — mirrors TODO.md `## Now`, currently empty. The backlog lives in `TODO.md`, tagged by area: `[mixer]` `[library]` `[downloads]` `[karaoke]` `[infra]`.)*

## Recent Sessions

### 2026-05-23
- ✅ **Doctrine conformance pass** via `/conform-project` (run 1 — created `conform-log.md`):
  - PLC structure tree: corrected stale paths `common/metadata_utils.py` → `common/load_from_music_app.py`, `library-management/rename_files.py` → `rename_music_file.py`, and the snake_case naming example.
  - PLC: corrected stale slash-command reference `/update-project-todos` → `/update-project-status`.
  - `PLANNING.md`: collapsed 10 granular dated karaoke implementation paragraphs into 2 milestone bullets (dual-rolling-log anti-pattern; detail lives in this log).
  - Archived the out-of-window `2026-02-18` session entry to `docs/SESSION-LOG.md` (retention rule).
  - Removed the empty `data/` directory (only an empty gitignored `data/exports/`) to Trash; trimmed its references from the PLC and README structure trees.
- ✅ **`PLANNING.md` Project Metadata**: set `Last Renamed: 2026-02-13`, and added `Todoist Project ID`/`Todoist Project Name` (see Todoist link below).
- ✅ **Genre/year tagging** via `/fill-missing-genres-years`: filled 5 tracks (Etienne Daho 1998, Janie 2020, Zaoui 2023, Brigitte 2015 → French; Yazoo "Don't Go" 1982 → New-Wave/Synth-Pop). "Genre or Year Blank" playlist now empty.
- ✅ **Todoist linked** via `/update-project-status`: created + linked a dedicated "YDJ Music Studio" Todoist project (ID `6ghVHmCJ3F5RJHhq`).
- ✅ **Created `TODO.md`** (first backlog file) with five inline area tags (`[mixer]` `[library]` `[downloads]` `[karaoke]` `[infra]`), triaged interactively. `## Now` empty; Next = library audit + mixer export-back; Later = BPM + Camelot-key tagging.
- ✅ **Dropped phase numbering** (design change): PLANNING `Strategy and Phases` → `Strategy and Breakdown` by the 5 areas; de-phased Success Criteria; stripped `(Phase C)`/`(Phase 5)` from decision headings; PLC `Completed Phases` → `Status by Area`; README `Development Status` → area bullets. Incidental phase mentions inside decision/risk bodies kept as historical record.
- ✅ **Restructured this log** to canonical `## Recent Sessions` + `### YYYY-MM-DD` subentries (resolves the `/update-project-status` freshness-scan misfire).
- No TODO.md `## Done` items to drain (TODO.md created empty this session).

### 2026-05-18
- ✅ **Doctrine conformance pass** via `/conform-project`:
  - Flipped stub read order in `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` to the canonical sequence (GLOBAL-CONTEXT → PROJECT-LOCAL-CONTEXT → PLANNING).
  - `PLANNING.md` Project Metadata block: removed the `**Status:** In Progress` line (deprecated 2026-05-18 — status lives only in the `## Status` checkboxes); unchecked the `Planning` checkbox so only `In Progress` is checked.
  - `PLANNING.md` Out of Scope: removed stale item "Direct Apple Music library write operations (deferred to Phase 4 for safety)" — Phase 4 shipped year + genre writes and they're in production.
  - PLC: added missing `## Current Priority / Next Actions` section, drafted from the open Phase 2/3 items in PLANNING (BPM/key audit, BPM tagging, mixer export-back, candidate-library re-enable).
  - PLC: added Phase 5 (Rust engine) to the Completed Phases list.
  - PLC: archived 7 older session entries (2026-02-14 through 2026-02-17 late-night) to new `docs/SESSION-LOG.md` per the 5-most-recent-OR-3-months retention rule. PLC keeps the 12 entries from 2026-02-18 onward (plus today).
- 📌 **Deferred (Tier 3, manual)**: `PLANNING.md` Project Metadata is still missing `Last Renamed:` (project was renamed DJ Music Library Manager → YDJ Music Studio) and carries a non-canonical `**GitHub:**` field that doctrinally belongs in PLC's External References.
- 📌 **Still drift-prone**: PLC's session log uses `## Recent Session (YYYY-MM-DD)` as separate top-level headings rather than the canonical single `## Recent Sessions` with `### YYYY-MM-DD` subentries. Left as-is for now — loose-match acceptable, restructuring would be churn.

### 2026-05-16
- 📌 **Karaoke folder read access**: Added `Read(//Users/fydupre/Music/Karaoke/**)` to project `.claude/settings.local.json` so Claude can read karaoke source files from `~/Music/Karaoke/` without per-prompt approval. Folder stays at its native location (not moved under the project).

### 2026-05-12
- ✅ **Mixer ascending-BPM presentation**: After Held-Karp/SA produces `global_overall_best_order`, `mixer/mixer.py` now computes mean BPM of the first half (`order[:n//2]`) vs second half (`order[n//2:]`) and reverses the order when the last half is lower. Justification: edge cost is symmetric (`harmonic_cost_from_keys` uses absolute Camelot distance; tempo cost uses `abs(bpm1 - bpm2)`), and shifts are stored per track-index (not per position), so reversal preserves the exact cost. Reversal logged to stdout when it happens. Skipped for `n < 2`.
- ✅ **Mixer per-run timestamped text export**: `mixer/mix_YYYY-MM-DD_HH-MM-SS.txt` written after the existing console output. Header lines (lines starting with `#`) include generation timestamp and cost breakdown; data rows have `Pos  BPM  Shift  OrigKey  EffKey  Artist - Title`. Path is resolved via `os.path.dirname(os.path.abspath(__file__))` so it always lands next to the script regardless of CWD. `.gitignore` gains `mixer/mix_*.txt` so per-run outputs don't clutter `git status`.

### 2026-05-10
- ❌ **Party Tyme YouTube playlist automation (abandoned)**: Attempted to automate discovery of Party Tyme karaoke videos on YouTube using YouTube Data API v3. Built `youtube_party_tyme_playlist.py` to read top-rated videos from Apple Music, search the Party Tyme channel, and optionally create a YouTube playlist of matches. Match quality was too poor to be useful (4/20 correct songs in testing). The Party Tyme channel (@partytymekaraokechannel6967) publishes both audio-only tracks AND full lyric videos — the search just couldn't reliably surface the lyric videos over the audio ones. The channel remains a valid manual source for karaoke videos; it's the automated search workflow that isn't worth the effort. Script removed. **Side benefit kept**: added `load_playlist_from_music_app()` + batched helpers to `common/load_from_music_app.py` — reads any named Apple Music playlist (including smart playlists) efficiently in 100-track batches rather than a single slow AppleScript loop. **GCP asset kept**: YouTube Data API v3 key in `~/.shared-scripts/.env` under GCP project "YDJ Music Studio"; may be useful for other YouTube automation.

### 2026-05-09
- ✅ **`--no-lut` mode**: Skips the grayscale + 3-band LUT step so multi-color text (per-singer colors in Party Tyme duets, background vocals) is preserved on a black background instead of being collapsed to a single sung color. Mask, `--bg-color`, `-z`, `--outline`, intro/outro all still apply. `-hi`, `--invert-bands`, `--sung-color` are silently ignored. New "Apply LUT" toggle in the GUI inline with the threshold-section header — when off, only the Low slider stays visible (relabeled "Black floor"); High, Invert bands, Sung-color picker hide.
- ✅ **Floor-to-black step in `--no-lut` mode**: Replaces the LUT's low-band quantization. `split → hue=s=0,lutrgb=if(lt(val,lo),0,255) → blend=multiply` — pixels below `-lo` go pure (0,0,0); pixels above keep their original color. Same `-lo` parameter as the LUT mode (no new flag). Without this, anti-aliased edges and bg-darken residue confused the outline chain's `gt(val,1)` text detector. **Side fix**: bg-darken's `lutyuv` step also pulls chroma toward neutral 128 by the same K factor — at DS=100 matched pixels become true black on their own. In LUT mode this chroma move is a no-op since the downstream `hue=s=0,lutrgb` overwrites chroma anyway. Filename token: `nolut` → `nolut-LO` (e.g. `nolut-40`).
- ✅ **Negative zoom**: `-z PERCENT` validation widened to `[-100, 100]` (was `> 0 and ≤ 100`). Negative branch uses `scale=iw*F:ih*F,pad=W:H:(W-iw)/2:(H-ih)/2:color=black` — text shrinks toward center, surrounded by pure black. Useful for Party Tyme channels where lyrics sit too close to frame edges. Filename token: `zoom-N` (positive, unchanged) or `zoomout-N` (negative). GUI slider range: `1...100` → `-20...20`.
- ✅ **v1 → consolidated rename (2026-05-09)**: `karaoke-processing/karaoke-process-v2` is now the single canonical script `karaoke-processing/karaoke-process`. The original v1 script (the basic mask + LUT pipeline) has been retired — feature parity reached and exceeded. Touched: 2 path strings in `App.swift`, 1 user-facing error message in `ContentView.swift`, the script's internal usage/help/example lines, the `karaoke-process.md` doc (drop "v2 Prototype" framing, replace with "Advanced Options"), `PROJECT-LOCAL-CONTEXT.md`, `README.md`, `PLANNING.md` (active prose only — historical Decision blocks left intact as record). Quick Action workflow renamed `Karaoke Process v2.workflow` → `Karaoke Process.workflow` (Info.plist NSMenuItem default updated; reinstalled in `~/Library/Services/`). Old v1 script + old workflow files moved to Trash per global "never `rm`" preference. App rebuilt and installed; smoke-tested via PATH binary.
- ✅ **Validation on Britney Spears - Criminal (Party Tyme channel)**: end-to-end matrix with `--no-lut --outline 2 -lo 50` (visible halo around multi-color text on pure-black bg), `--no-lut --bg-color 130FE6 --bg-strength 95 --outline 2` (default lo=40 sufficient — bg-darken pushes luma well below 40), `--no-lut -lo 50 -z -10 --outline 2` (text shrunk into black padding, halo+floor intact), and LUT-on regression (`-lo 40 -hi 200 --invert-bands` unchanged). One discovered constraint: Party Tyme's blue background has luma ~41 after `hue=s=0`, just barely above default `lo=40`. So default `lo` doesn't push bare blue to black on its own — same dynamic as default LUT (which mapped the same blue to white, not black). Recommend `lo ≥ 50` or enable bg-darken. Documented in karaoke-process.md.
- ✅ **GUI Refresh Previews pipe-deadlock fix**: `PreviewService.ShellRunner.run` blocked forever on stderr-heavy source files. Mechanism: macOS `Pipe()` buffers hold ~64 KB; the old code only read them inside `terminationHandler`. ffmpeg dumps full input-file metadata to stderr on every invocation; the script runs ffmpeg twice for previews (mask PNG + processed PNG). Files with embedded Serato/MixedInKey markers (Dire Straits - Money For Nothing karaoke source) emitted ~38 KB stderr per call → ~76 KB total → buffer fills → ffmpeg blocks on write → terminationHandler never fires → GUI spins. Reproduced with a standalone Swift program using the old pattern (timed out past 30 s); confirmed fix reaches 0.322 s with both PNGs produced. **Fix:** drain both pipes incrementally via `readabilityHandler` accumulating into a small `PipeBuffers` reference-typed helper (kept the buffers off captured local vars so Swift 6 sendable-capture rules don't fire warnings; chose a class over `actor` to keep the call sites synchronous and minimize churn). Same approach `ProcessService` already used for the full encode path. Aspect ratio (4:3 vs the user's usual 16:9 sources) is a coincidence — the real trigger was metadata volume; this video happened to be 4:3 *and* metadata-heavy. **GUI binary**: `/Applications/KaraokeProcessGUI.app` updated to the fix; old app moved to `~/.Trash/KaraokeProcessGUI.app.<timestamp>` per global "never `rm`" rule.
- 📌 **Test asset**: `docs/Dire Straits - Money For Nothing [Karaoke].mp4` is the canonical reproducer for stderr-heavy karaoke sources. Stays in `docs/` (gitignored via `*.mp4`).

### 2026-05-08
- ✅ **Mask-margin-zero bug fix in `karaoke-process-v2`**: Setting any margin to 0% (via CLI or GUI slider) produced an entirely black "masked" preview/output. Root cause: ffmpeg's `drawbox` documents that `w=0` or `h=0` is interpreted as the full input dimension, so a strip with a zero side painted the whole frame black. The script previously emitted four `drawbox` calls unconditionally (top/bottom/left/right strips, or four corners with `--corners-only`); when a side was 0, the corresponding strip's width or height was 0 → full-frame fill. Fix: build `mask_filter` from non-empty strips only; if all four margins are 0, fall back to a passthrough `null` filter. Same logic applied to the `--corners-only` path. Verified with synthetic input (red 320x240): all-zero margins pass through; mixed zero/non-zero margins mask only the requested sides; defaults (5/15/15/5) unchanged.
- ✅ **CLI rename + outro support**: dropped `-splash` (v2 was still in validation, GUI is the only consumer). Added four flags: `--intro-preserve N`, `--intro-blackout N`, `--outro-preserve N`, `--outro-blackout N`. Each `*-preserve`/`*-blackout` pair errors out if both are passed (instead of silent precedence); `intro_secs + outro_secs < duration` enforced. Filter chain refactored into a generalized concat builder: each side may produce an `[intro]` or `[outro]` branch (preserve = trim only; blackout = trim + `drawbox=...:fill` covering the full frame); the body branch trim becomes `start=intro_secs:end=duration−outro_secs` with the relevant fields omitted when one side is off. Audio is still mapped from `0:a:0` and stream-copied — the rebuilt video timeline matches the original audio. Filename tokens: ` intro-keep-N` / ` intro-bo-N` / ` outro-keep-N` / ` outro-bo-N`. Validated with the matrix: preserve+preserve, blackout+blackout, mixed, intro-only, outro-only, no-flags, both error paths, duration overflow, still-frame ignore note, and the bg-darken+outline+intro+outro stack. Mask-zero fix and intro/outro feature shipped in the same commit.
- ✅ **GUI Intro/Outro UI**: replaced the single "Splash" section with parallel **Intro** and **Outro** sections in the right column. Each: enable toggle (autocaptures from playhead — Intro = `currentSeconds`, Outro = `duration − currentSeconds`), duration text field, horizontal **Preserve | Blackout** radio group. New `IntroOutroMode` enum (preserve/blackout). `cliArgs(includeIntroOutro:)` (renamed from `includeSplash:`) emits the right flag based on mode. Old `splashEnabled` / `splashSeconds` / `introBlackoutEnabled` fields removed from `ProcessingParameters`; presets always saved those defaulted to false/5/false, so old preset files decode cleanly to new defaults via `decodeIfPresent`. Preset semantics unchanged: intro/outro params are carried over (not overwritten) when applying a preset, and reset to defaults before saving.
- 📌 **GUI binary location**: `/Applications/KaraokeProcessGUI.app` updated to the intro/outro build. Old app moved to `~/.Trash/KaraokeProcessGUI.app.<timestamp>` (per global "never `rm`" preference).

### 2026-05-07 (evening)
- ✅ **Background darken feature for `karaoke-process-v2` + GUI**: Optional pre-LUT pass that pushes pixels matching a target color toward black so the LUT can quantize colored Karafun backgrounds (deep blue, olive, orange) into the low-luminance bucket. **Script:** 4 new flags — `--bg-color HEX` (activator), `--bg-strength N` (DS, 0-100, default 85), `--bg-range N` (CR, 0-100, default 35), `--bg-blend N` (default 10). Pipeline insertion: `mask → bg-darken → zoom → grayscale → LUT → outline`; splash branch unaffected. When bg-darken is active, the script always uses `filter_complex` (split/overlay needs labeled pads); when off, the existing `-vf` simple-chain path is preserved. Filename token: ` bg-RRGGBB-DSnn-CRnn-BLnn`. **GUI:** new "Background darken" section in `ParametersPanel` left column (between Margins and Zoom — matches pipeline order) with checkbox + SwiftUI `ColorPicker` (uses standard macOS color panel with built-in eyedropper for sampling video pixels) + 3 sliders. Default bg color `0040C0` (representative blue) used on first activation; subsequently it remembers last pick. Models gained 5 new fields (`bgDarkenEnabled`, `bgColor`, `bgStrength`, `bgRange`, `bgBlend`), all decoded with `decodeIfPresent ?? default` so existing presets keep working and new presets persist all 5 fields.
- 📌 **Filter design pivot mid-implementation**: Originally wired up with `hsvkey` (matches our `docs/bg-removal-tests/` validation scripts), but discovered during CLI integration testing that `hsvkey` is broken in ffmpeg 8.1 — even when the input pixel exactly matched the target hue/sat/val, the alpha output stayed at 255. Confirmed by direct testing on a pure-blue PNG: `hsvkey hue=242 sat=0.64 val=0.72 similarity=0.10` produced mean alpha 255 (no keying); `colorkey color=0x4742B8 similarity=0.10` produced mean alpha 0 (full key). Switched to `colorkey` (RGB-distance based). Re-validated bg-darken end-to-end on Depeche Mode video at frame 120s with `--bg-color 4742B8 --bg-strength 95 --bg-range 35` — bg goes pure black, lyrics render cleanly through the LUT. **CR slider mapping:** `colorkey`'s useful similarity range on Karafun frames is 0.05-0.20 (text edges start eating around 0.20). Mapped CR (0-100%) → similarity (0.01-0.30) linearly so the user's earlier intuition ("35% works") still gives a sensible result (~0.11) and the full slider range stays meaningful.
- 📌 **Backstory — earlier "successful" hsvkey tests were a mirage**: Across a long sequence of `docs/bg-removal-tests/` sweeps we'd locked in DM=CR35/DS95, C=CR45/DS95 etc. with hsvkey and saw what looked like darkening in the inline previews. Post-mortem: hsvkey at sim≈0.35 keys ~3% of pixels (alpha mean ~252 of 255) on a pure-blue input, so the dim layer barely showed through. The visual difference between settings was real but tiny; we ascribed more to it than was there. The colorkey switch revealed the actual full-strength behavior. Validation images confirming the new chain are in `docs/v2-cli-tests/`.
- ✅ **Documentation updates**: `karaoke-process.md` gained a `--bg-color` section under the v2 prototype docs; "Output Naming" section updated with a bg-darken filename example.
- 📌 **Test artifact location**: bg-darken FFmpeg validation lives in `docs/bg-removal-tests/` (12 final PNGs from `run_ds_sweep.sh` plus 6 `DS95_CR{35,45}` follow-ups, all gitignored — local working set only). Script-level CLI tests in `docs/v2-cli-tests/` (still-frame and splash-mode encodes for DM/C). Both folders untracked; nothing committed in `docs/`.
- 📌 **GUI binary location**: `/Applications/KaraokeProcessGUI.app` updated to the bg-darken build. Old app moved to `~/.Trash/KaraokeProcessGUI-pre-bgdarken-<timestamp>.app` (per global "never `rm`" preference).

### 2026-05-07
- ✅ **GUI splash auto-capture bug fix**: When user toggled "Preserve intro splash" with the playhead at e.g. 5 s, the captured splash duration was a stale fraction (e.g. 0.5 s) instead of 5.00 s. Root cause: `ContentView` held `AVPlayerWrapper` as plain `@State`, so updates to `@Published var currentSeconds` did NOT trigger `ContentView` re-renders; the snapshot `currentPlayheadSeconds: player.currentSeconds` passed into `ParametersPanel` was therefore captured at some earlier render and never refreshed. The Refresh-Previews button was unaffected because its action reads `player.currentSeconds` directly inside the closure. **Fix:** `ParametersPanel` now takes `player: AVPlayerWrapper` as `@ObservedObject` (replacing the two `Double` snapshot params), and reads `player.currentSeconds` / `player.durationSeconds` live in the splash-toggle `onChange` and the bottom `t = ...` readout. The bottom readout had the same staleness issue and is now also live.
- ✅ **Delete preset**: New destructive item in the Preset dropdown menu — `Delete preset "{name}"…` — appears only when `currentPreset == .named(name)`. Since any parameter edit flips `currentPreset` back to `.custom` (via `userTouchedParameters`), this condition is equivalent to "a preset is currently selected and unmodified", which is what the user requested. Implementation: `PresetStore.delete(name:)` removes from the in-memory dict + persists; `PresetDeleteDialog.runConfirmation(name:)` is an `NSAlert` with Delete/Cancel buttons (warning style). On confirm, preset is deleted, `currentPreset` flips to `.custom`, and current parameters stay put. Built-in presets (Sing King, Musisi) ARE deletable — they only seed on first launch (when `presets.json` is absent), so deleting them is permanent unless the user removes the JSON file. User accepted this tradeoff implicitly by not flagging built-ins as protected.
- 📌 **Verified**: rebuilt via `./build.sh`, sent old `/Applications/KaraokeProcessGUI.app` to Trash (`KaraokeProcessGUI-pre-deletefix-*.app`), installed new build. User confirmed both fixes working end-to-end.

### 2026-05-03
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

### 2026-05-02
- ✅ **`karaoke-process-v2` prototype**: parallel script alongside the original `karaoke-process` (kept untouched). All v1 functionality preserved.
- ✅ **`-splash SECONDS`**: single-pass `concat` filter inside `filter_complex` — splash branch trims `[0:v]` to `[0,N)`, body branch trims `[N,end]` and runs the mask+LUT chain, then both concat. Audio is stream-copied (`-c:a copy -map 0:a:0`) so it's bit-perfect, no AAC frame-boundary issues. Accepts decimals. Verified on ROSÉ & Bruno Mars - APT (5s splash → splash-5; also tested at 4.5s).
- ✅ **`-z PERCENT`**: `scale=iw*z:ih*z, crop=W:H` after the mask, before the grayscale+LUT. Output dims unchanged. Verified that filter ordering matters — running the LUT *after* the scale keeps the output deterministic (3 colors), running it before would produce gray/dark-green pixels at scaled text edges.
- ✅ **`--invert-bands`**: swaps mid/high outputs in the LUT — `< lo → black`, `lo ≤ val < hi → green`, `≥ hi → white`. Rescues Party Tyme-style channels. Filename token changes from `bwg-LO-HI` to `bgw-LO-HI`. Validated on APT (`-lo 40 -hi 200 --invert-bands`): orange sung renders green, white unsung renders white.
- ✅ **`-splash` × `-f` interaction**: in still-frame mode, `-splash` is ignored with a notice (still-frame is for tuning, not segment-aware).
- ✅ **`--outline N` integrated** (default 2; 0 disables): stacked-offset gray copies for a neon-style two-ring halo. Inner stamps at ±N (gray 80), outer stamps at ±2N (gray 220), 8 compass directions, alpha-composited so the colored text core is preserved. Filter-chain slot: after LUT, before encode. Splash branch stays unaltered (outline lives only in body branch). When N=0, outline chain is skipped and the script falls back to the simpler `-vf` path. End-to-end validated on APT (full re-encode with `--outline 2 -splash 4.5 -z 10 --invert-bands --corners-only -t 0% -r 0% -b 30% -l 15%`): duration matches original, audio bit-perfect, splash untouched, body has visible 4px halo. Performance: ~3-4x slower than no-outline due to 16 overlay stamps per frame.
- ✅ **APT (Party Tyme) added as channel reference** in `karaoke-process.md`. Old "do not run" guidance for Party Tyme replaced with `--invert-bands` recipe.
- ✅ **Working folder relocated**: ~2GB karaoke-production assets moved into `docs/karaoke-production/`. `*.mp4` was already gitignored, so videos won't sync.
- 📌 **Test artifacts**: outline experiment PNGs and APT v2 test outputs live directly under `docs/` (per project convention "save test images/videos under docs, not /tmp").

### 2026-04-29
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

### 2026-04-28
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

_Earlier entries (2026-02-18 and before) archived to `docs/SESSION-LOG.md`._

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
- Python modules: snake_case (e.g., `apple_music.py`, `load_from_music_app.py`)
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
│   ├── load_from_music_app.py     # Batched Apple Music playlist reader
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
│   ├── rename_music_file.py       # File renamer based on metadata
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
- `karaoke-processing/karaoke-process` - Bash + ffmpeg script (single canonical version; v1 prototype retired 2026-05-09). Full feature set: `--intro-preserve` / `--intro-blackout` / `--outro-preserve` / `--outro-blackout` (independent intro/outro segment handling, mutually exclusive within each side; concat builder produces 0/2/3-way concat depending on what's active), `-z` (zoom; positive = scale up + crop, negative = scale down + center-pad with pure black), `--invert-bands`, `--outline N`, `--no-lut` (skip LUT, use `-lo` as floor-to-black threshold), `-o OUTPUT_DIR`, `--sung-color HEX`, `--bg-color HEX` + `--bg-strength` / `--bg-range` / `--bg-blend` (background darken via `colorkey`; lutyuv step also neutralizes chroma). Mirrored to `~/.local/bin/karaoke-process`.
- `karaoke-processing/karaoke-process.md` - Authoritative reference: goal/rationale, options, defaults, still-frame mode, output naming, channel-specific starting points (Musisi/Sing King/Party Tyme/APT), advanced-options section (intro/outro, zoom, invert-bands, outline, bg-color, no-lut), GUI app section, tuning workflow
- `karaoke-processing/karaoke-process-gui/` - SwiftUI macOS app source. SPM executable target. Build via `./build.sh` → `KaraokeProcessGUI.app` (ad-hoc codesigned). Sources: `App.swift` (entry + AppDelegate + AppState singleton + script discovery), `ContentView.swift` (top-row split + bottom-row split + status row), `ParametersPanel.swift` (2-col params + bottom Refresh bar + ColorPickers for sung-color and bg-color + Background darken section + Intro section + Outro section + Apply LUT toggle inline with thresholds header; observes `AVPlayerWrapper` directly so playhead reads are always live), `VideoPanel.swift` (NSViewRepresentable around AVPlayerView + AVPlayerWrapper with currentSeconds/durationSeconds/videoAspectRatio), `PreviewPanel.swift` (NSImage display with optional aspect-ratio white border), `Models.swift` (ProcessingParameters + Codable + CurrentPreset enum + IntroOutroMode enum; bg-darken + intro/outro + applyLut fields included), `Presets.swift` (PresetStore JSON persistence + save/delete + PresetSaveDialog + PresetDeleteDialog NSAlert flows; bg-darken + applyLut fields persist; intro/outro fields excluded from saved presets), `PreviewService.swift` (shells `karaoke-process -f -o cacheDir`, parses Created: paths from stdout, returns NSImages), `ProcessService.swift` (foreground Process with stderr streaming, `time=` regex parsing for progress bar, terminationHandler for cleanup).
- `karaoke-processing/Karaoke Process.workflow/` - Automator Quick Action: single Run-Shell-Script action that calls `open -a /Applications/KaraokeProcessGUI.app "$f"` for each selected movie. Restricted to movie file types. Install: `cp -R "Karaoke Process.workflow" ~/Library/Services/`. Right-click any video in Finder → Quick Actions → "Karaoke Process".
- `karaoke-processing/PROCESS PARTY TYME.workflow/` - Legacy reference workflow encoding the blue-background chromakey trick (drawbox blue cover + `colorkey=0x130FE6` over black). Now subsumed by `--no-lut` + `--bg-color` workflow; kept for historical reference.
- `karaoke-processing/Replace Lower Left Corner w BK (Sing King).workflow/` and `Replace Lower Right Corner w BK (Sing King).workflow/` - Legacy reference workflows for Sing King logo masking (now superseded by `--corners-only` + margin tuning).
- `~/Library/Application Support/KaraokeProcessGUI/presets.json` - User-saved processing presets (pretty-printed JSON, sorted-keys). Seeded with Sing King + Musisi on first launch; user owns it after that.
- `~/.local/bin/karaoke-process` - Installed canonical script (PATH-accessible from anywhere)
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
- `/update-project-status` — Session-start sync (Todoist reconcile, light freshness checks)

## Notes
- Smart playlist "Genre or Year Blank" drives the missing-metadata tagging workflow
- "Ignore year or genre inconsistencies" playlist filters out already-resolved groups
- Interactive scripts (`tag_tracks.py`, `resolve_tagger.py`) require a real TTY — run via `run-tagger.sh` / `run-resolver.sh`
- XML export (`~/YDJ Library.xml`) used for bulk detection; AppleScript used for reads/writes
