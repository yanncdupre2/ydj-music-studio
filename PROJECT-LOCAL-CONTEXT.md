# Project Specific Context

## Purpose
Comprehensive DJ music production and library management system for YDJ, encompassing playlist optimization (harmonic mixing), Apple Music library metadata management, and YouTube media processing.

## Current Priority
**Phase 3: Mixer Improvements** (SA optimization done, DOE complete, Rust engine next)

## Completed Phases
- ✅ **Phase 1:** Foundation & Organization — modular structure, genres.json, Git/GitHub
- ✅ **Phase 4:** AppleScript integration — direct year/genre updates to Apple Music working

## Recent Session (2026-02-17, evening)
- ✅ DOE for SA annealing parameters completed: 9 variations (init temp 300/500/700 × final temp 0.05/0.1/0.15), 879 total attempts
- ✅ **DOE conclusion**: nominal values (500 → 0.1, 410k iterations) confirmed optimal — no variation statistically better
- ✅ **Key insight**: solution quality is driven by random initial arrangement, not temperature schedule (Pearson r = -0.135)
- ✅ Time budget increased from 3 to 5 minutes (~80 attempts for 17 tracks)
- ✅ DOE results saved to `mixer/doe_temperature_results.csv` (879 rows)
- ✅ `DOE-ANNEALING-PARAMS.md` updated with full findings
- **Next**: Rust SA engine (Phase 5) for 50-100x speedup

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
│   ├── process_mkv.sh             # Video classification (real vs static image)
│   ├── convert_mkv_to_mp4.sh      # Lossless remuxing
│   ├── reencode_mkv_to_mp4.sh     # Transcoding for incompatible codecs
│   ├── reencode_all_mkv.sh        # Batch transcoding
│   ├── convert_opus_to_aac.sh     # Opus→AAC audio conversion
│   └── README.md
│
├── data/                          # Working data files
│   ├── exports/                   # Apple Music XML exports (gitignored)
│   ├── cleaned_music_library.csv  # Legacy (can archive)
│   └── your_music_library.csv     # Legacy (can archive)
│
├── venv/                          # Python virtual environment (gitignored)
├── docs/                          # Additional documentation
└── src/                           # Future: compiled Rust binaries
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
- `mixer/mixer.py` - SA optimizer: reads "Mixer input" playlist, time-budgeted annealing, bridge key hints
- `mixer/OPTIMIZER-PLAN.md` - Python + Rust optimization roadmap
- `mixer/DOE-ANNEALING-PARAMS.md` - Experiment plan for tuning SA parameters
- `common/apple_music.py` - XML reader + AppleScript playlist management (BPM/Comments/Rating fields)
- `common/genres.json` - Canonical 31-genre taxonomy

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
```

### Mixer Usage (Current)
```bash
cd ~/Projects/ydj-music-studio
source venv/bin/activate
python3 mixer/mixer.py
# Reads from "Mixer input" Apple Music playlist, optimizes for 5 minutes
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
