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

## Recent Sessions

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

### 2026-06-14
- ✅ **Doctrine conformance pass** via `/conform-project` (run 2) — 3 findings, all fixed:
  - PLC §2.6 — collapsed the Current Priority empty-state to the canonical minimal form `*(none — mirrors TODO.md ## Now)*` (was verbose with area-tag legend + backlog-location hint; drift-prone per doctrine).
  - PLC §2.9.5 — qualified `sources/musicbrainz.py` → `library-management/sources/musicbrainz.py` in External APIs (consistency with the Key Files entry).
  - TODO.md line 12 — auto-fixed `non-ascii:em-dash` on the metadata-quality audit item: `—` → ` - `.
- ✅ **Added Doctrine Compliance stamp** at EOF of PROJECT-LOCAL-CONTEXT.md (`v2.1`, `2026-06-14`) per DOCTRINE.md §8.1.
- ✅ **conform-log.md** — appended run 2 entry; bumped frontmatter to `last_conformed: 2026-06-14`, `conform_runs: 2`.
- 📌 **Improvements landed since run 1** (informational, not findings this pass): Project Metadata's `Last Renamed` populated, Todoist Project ID/Name present, and the Recent Sessions log already restructured to canonical `## Recent Sessions` + `### YYYY-MM-DD` (resolved a "still drift-prone" item from run 1).
- No TODO.md `## Done` items to drain (no completions this session).

### 2026-06-27 — Session close

<!-- gtd-session: 238bfc81-c404-491a-bbd1-6f766ecc299e -->

**Outcomes:**
- Implemented mixer export-back to Apple Music (mixer/mixer.py --export); verified live end-to-end with order preserved.
- Reworked the per-run mix report into Markdown (mixer/mixes/mix_*.md), persisting per-track key shifts and bridge/insertion recommendations.
- Fixed literal backslash-u escape sequences in PROJECT-LOCAL-CONTEXT.md that blocked the gtd session-close transaction.

**Decisions:**
- Export is opt-in via --export, not automatic, to respect the project's safety-first stance on live-library mutation.
- Exported playlists use a timestamped name to avoid duplicate-append and to match the mix-file scheme.
- One always-written Markdown artifact per run (not a separate companion doc); the .txt report format is retired.
- Generated mixes live in a dedicated gitignored mixer/mixes/ folder.

**Completed tasks:**
- [mixer] Export the optimized order back to Apple Music as a new playlist

**Unresolved:**
- Underlying gtd-system bug: session-close regex replacement chokes on literal backslash-u text in retained Recent Sessions entries; to be fixed in the gtd tool separately.
- mixer/CLAUDE.md still lists export-back under Future Development - fold into next /rebaseline-project.
- Cosmetic: Shift column renders +0 for unshifted tracks (consistent with console; leave or blank-out later).
- Two test playlists remain in Apple Music for the user to delete at leisure.

**Possible next-session objectives:**
- [library] Audit metadata quality - surface tracks missing BPM or key data (recommended)
- [infra] Apple Music backup/restore workflow before bulk library writes

### 2026-07-18 — Session close

<!-- gtd-session: f8ed7c0f-48a0-41eb-86ef-ca9ab2b6e0ff -->

**Outcomes:**
- Normalized Recent Sessions oldest-to-newest and archived entries beyond the configured retention limits.

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
- ✅ MusicBrainz: Release dates, genres (integrated in `library-management/sources/musicbrainz.py`, 1 req/sec rate limit)
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
