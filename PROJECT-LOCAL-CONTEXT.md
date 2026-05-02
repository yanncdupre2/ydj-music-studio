# Project Specific Context

## Purpose
Comprehensive DJ music production and library management system for YDJ, encompassing playlist optimization (harmonic mixing), Apple Music library metadata management, and YouTube media processing.

## Current Priority
**Karaoke video processing pipeline (v2 in progress)**: prototype `karaoke-processing/karaoke-process-v2` adds three new options on top of the v1 luminance-LUT pipeline: `-splash SECONDS` (preserve intro splash unaltered), `-z PERCENT` (uniform centered zoom for readability), and `--invert-bands` (swap mid/high LUT bands — rescues Party Tyme and APT-style channels where unsung text is brighter than sung text). A fourth option `--outline N` is in design: stacks 8 offset gray copies of the LUT'd text at offsets N and 2N to produce a two-ring "neon" halo (dark inner + bright outer), composited via alpha so the colored text core stays clean. Once outline is integrated and validated, v2 replaces v1 (which currently lives globally at `~/.local/bin/karaoke-process`).

## Completed Phases
- ✅ **Phase 1:** Foundation & Organization — modular structure, genres.json, Git/GitHub
- ✅ **Phase 4:** AppleScript integration — direct year/genre updates to Apple Music working

## Recent Session (2026-05-02)
- ✅ **`karaoke-process-v2` prototype**: parallel script alongside the original `karaoke-process` (kept untouched). All v1 functionality preserved.
- ✅ **`-splash SECONDS`**: single-pass `concat` filter inside `filter_complex` — splash branch trims `[0:v]` to `[0,N)`, body branch trims `[N,end]` and runs the mask+LUT chain, then both concat. Audio is stream-copied (`-c:a copy -map 0:a:0`) so it's bit-perfect, no AAC frame-boundary issues. Accepts decimals. Verified on ROSÉ & Bruno Mars - APT (5s splash → splash-5; also tested at 4.5s).
- ✅ **`-z PERCENT`**: `scale=iw*z:ih*z, crop=W:H` after the mask, before the grayscale+LUT. Output dims unchanged. Verified that filter ordering matters — running the LUT *after* the scale keeps the output deterministic (3 colors), running it before would produce gray/dark-green pixels at scaled text edges.
- ✅ **`--invert-bands`**: swaps mid/high outputs in the LUT — `< lo → black`, `lo ≤ val < hi → green`, `≥ hi → white`. Rescues Party Tyme-style channels. Filename token changes from `bwg-LO-HI` to `bgw-LO-HI`. Validated on APT (`-lo 40 -hi 200 --invert-bands`): orange sung renders green, white unsung renders white.
- ✅ **`-splash` × `-f` interaction**: in still-frame mode, `-splash` is ignored with a notice (still-frame is for tuning, not segment-aware).
- 🚧 **`--outline N` in design**: stacked-offset gray copies for a neon-style two-ring halo. Inner stamps at ±N (gray 80), outer stamps at ±2N (gray 220), 8 compass directions, alpha-composited so the colored text core is preserved. Prototyped via ad-hoc `ffmpeg filter_complex` on a single frame — visually validated. Filter-chain slot: after LUT, before encode. Splash branch stays unaltered. Not yet integrated into v2 script — that's the next step.
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
- `karaoke-processing/karaoke-process-v2` - Prototype with new options: `-splash`, `-z`, `--invert-bands` (and `--outline` planned). Will replace v1 once outline is integrated and validated.
- `karaoke-processing/karaoke-process.md` - Authoritative reference: goal/rationale, options, defaults, still-frame mode, output naming, channel-specific starting points (Musisi/Sing King/Party Tyme/APT), v2 prototype section, `--outline` roadmap, tuning workflow
- `~/.local/bin/karaoke-process` - Installed copy of v1 (PATH-accessible from anywhere); v2 is run from the project tree until promoted
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
