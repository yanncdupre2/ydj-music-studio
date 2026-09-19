# Project Specific Context

## Purpose
Comprehensive DJ music production and library management system for YDJ, encompassing playlist optimization (harmonic mixing), Apple Music library metadata management, and YouTube media processing.

**Karaoke video processing pipeline**: `karaoke-processing/karaoke-process` is the single canonical script (the v1 prototype was retired 2026-05-09 once the consolidated script reached feature parity). On top of the basic luminance-LUT pipeline it offers: independent intro/outro segments via `--intro-preserve N` / `--intro-blackout N` / `--outro-preserve N` / `--outro-blackout N` (each side can preserve the segment unaltered or replace it with a fully black frame; pairs mutually exclusive; intro+outro must sum < duration); `-z PERCENT` (uniform centered zoom; positive = scale up + center-crop, negative = scale down + center-pad with pure black, range -100…100); `--invert-bands` (swap mid/high LUT bands — rescues Party Tyme/APT-style channels); `--outline N` (high-contrast two-ring gray halo, default 2); `--no-lut` (skip the LUT entirely; preserve multi-color text on a black background — useful for Party Tyme duets where different singers use different font colors; uses `-lo` as a floor-to-black threshold instead of the LUT low band); `-o OUTPUT_DIR` (redirect outputs); `--sung-color HEX` (customizable sung-text color, default `00C800`); and `--bg-color HEX` + `--bg-strength` / `--bg-range` / `--bg-blend` (optional background darken for Karafun-style colored backgrounds; bg-darken's `lutyuv` step also pulls chroma toward neutral 128 so matched pixels actually go to true black even without the LUT). Pipeline insertion order in body: `mask → bg-darken → zoom → (LUT or floor-to-black) → outline`; intro/outro branches stay untouched. The filter chain is a 3-way concat `[intro][body][outro]` (or 2-way / no-concat depending on which sides are active). A SwiftUI macOS app `karaoke-processing/karaoke-process-gui/` wraps the script with live previews, persisted presets (including bg-darken and applyLut fields), white aspect-ratio borders on all image panels, and a foreground progress bar driven by parsing ffmpeg stderr. Quick Action Automator workflow at `karaoke-processing/Karaoke Process.workflow/` invokes the app via Finder right-click. End-to-end validated on ROSÉ & Bruno Mars - APT (LUT mode), Depeche Mode/Christophe/Frank Sinatra Karafun samples (LUT + bg-darken), and Britney Spears - Criminal (Party Tyme, --no-lut + bg-darken + outline + zoomout).

## Status by Area
- **Mixer:** Rust SA + Held-Karp engine shipped (throughput measured 60x once, 2026-02-17, on a 17-track playlist (0.2 → 12.0 attempts/s) — a single benchmark, not a general guarantee; exact for n ≤ 20); live "Mixer input" reading, timestamped Markdown mix report, and opt-in `--export` write-back to a new Apple Music playlist (shipped 2026-06-27). **Open:** the input playlist name is still a string literal at `mixer/mixer.py:221` (`load_playlist_from_app("Mixer input")`) — track lists are no longer hardcoded, but the playlist name is.
- **Library:** 4-source genre/year tagging, inconsistency resolver, and live AppleScript year+genre writes in production. Open: BPM/key audit + fill.
- **Downloads:** complete — yt-dlp rename + MKV→MP4 / Opus→AAC conversion.
- **Karaoke:** `karaoke-process` script + SwiftUI GUI mature and in use.
- **Infra:** shared `common/` utils, genre taxonomy, venv + Rust build in place. Open: Apple Music backup/restore workflow.

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
├── PLANNING.md                    # Identity, objective, scope, durable decisions
├── TODO.md                        # Canonical tasks (machine-maintained)
├── PROJECT-LOCAL-CONTEXT.md       # This file (how/where/with what)
├── SESSION-LOG.md                 # Session history (read via `gtd session context`)
├── ARCHIVE/SESSION-LOG.md         # Older session entries, oldest first
├── AGENTS.md                      # Agent entry point (read order)
├── CLAUDE.md                      # Provider redirect → AGENTS.md
├── README.md                      # User-facing overview
├── requirements.txt               # Python dependencies
├── .gtd/config.toml               # GTD project config (portfolio root, sources)
├── .gitignore                     # Exclude venv, data, media
│
├── common/                        # Shared utilities across subprojects
│   ├── apple_music.py             # XML reader + AppleScript playlist/metadata access
│   ├── load_from_music_app.py     # Batched Apple Music playlist reader
│   ├── genres.json                # Canonical 31-genre taxonomy
│   └── README.md
│
├── mixer/                         # Playlist optimization engine
│   ├── CLAUDE.md                  # Mixer-specific AI context
│   ├── mixer.py                   # Simulated annealing optimizer
│   ├── camelot.py                 # Camelot wheel system
│   ├── create_key_playlists.py    # One-time Candidates-playlist setup utility
│   └── README.md
│
├── library-management/            # Tagging, cleanup, organization
│   ├── CLAUDE.md                  # Library mgmt AI context
│   ├── cleanup.py                 # Discrepancy finder and resolver
│   ├── rename_music_file.py       # File renamer based on metadata
│   ├── research_tracks.py         # 4-source metadata research
│   ├── tag_tracks.py              # Interactive keypress tagger (live writes)
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
│   ├── karaoke-process-gui/       # SwiftUI front-end (installed at /Applications/KaraokeProcessGUI.app)
│   └── karaoke-process.md         # Authoritative reference: goal/rationale, usage, options, channel-specific starting points, tuning workflow
└── src/
    └── ydj_mixer_engine/          # Rust SA + Held-Karp engine
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
`run-mixer.sh` is the supported entry point — it sources `~/.cargo/env` and the
venv before running, so the Rust engine is importable.
```bash
cd ~/Projects/ydj-music-studio
./run-mixer.sh              # default 5-minute time budget
./run-mixer.sh 2            # 2-minute budget (positional, float minutes)
./run-mixer.sh 0.5 --export # quick run + write the order back to Apple Music
# Reads from the "Mixer input" Apple Music playlist.
# Uses Rust engine (ydj_mixer_engine) if built; Python fallback otherwise.
# --export is opt-in. It creates a NEW playlist "Mixer output <timestamp>";
# it never mutates the input playlist. On partial failure it reports the
# added/failed counts and does not roll back the tracks already added.
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

Project-local commands (defined in `.claude/commands/`):
- `/fill-missing-genres-years` — End-to-end workflow: research → LLM/web fill → interactive tagging
- `/resolve-inconsistencies` — Detect and resolve year/genre conflicts across track variants (229 groups reported at first detection, 2026-02-14)

Session lifecycle is owned by the installed GTD skills, not by this project:
`gtd-start-session` to open, `gtd-finish-session` to close (it owns TODO
regeneration, commit, push and session-log retention), `gtd-review-project`
for a strategic review. The retired `/rebaseline-project` and
`/update-project-status` commands no longer exist.

## Notes
- Smart playlist "Genre or Year Blank" drives the missing-metadata tagging workflow
- "Ignore year or genre inconsistencies" playlist filters out already-resolved groups
- Interactive scripts (`tag_tracks.py`, `resolve_tagger.py`) put a single-keypress
  prompt (`1` / `2` / `S`) in front of every live AppleScript write — verified in
  `library-management/tag_tracks.py:151` immediately before the
  `update_track_metadata()` call. `getch()` calls `tty.setraw()`, so they need a
  real TTY: launch `run-tagger.sh` / `run-resolver.sh` in a **new Terminal
  window** via `osascript`, never inline in an agent shell. The `osascript`
  invocations live in the two `.claude/commands/` files.
- XML export (`~/YDJ Library.xml`) used for bulk detection; AppleScript used for reads/writes
