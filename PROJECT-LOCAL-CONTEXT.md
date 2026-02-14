# Project Specific Context

## Purpose
Comprehensive DJ music production and library management system for YDJ, encompassing playlist optimization (harmonic mixing), Apple Music library metadata management, and YouTube media processing.

## Current Priority
**Phase 1: Foundation & Organization**

1. **Organize existing YDJ folder contents into modular structure**
   - Move existing scripts from ~/Projects/YDJ/ into organized subfolders
   - Create mixer/, library-management/, downloads/, common/, data/ structure
   - Preserve existing functionality during migration

2. **Extract and store canonical genre taxonomy**
   - Create `common/genres.json` with 31 compound genres from Apple Music library
   - Use exact genre strings as they appear (20+ songs threshold)

3. **Set up Python environment and Git repository**
   - Fresh venv with requirements.txt
   - Initialize git, create .gitignore (venv, CSV, XML, media files)
   - Push to GitHub: https://github.com/fydupre/ydj-music-studio

## Recent Session (2026-02-13)
- ✅ Renamed project from "DJ Music Library Manager" to "YDJ Music Studio"
- ✅ Updated idea document with comprehensive features and phases
- ✅ Created project scaffold at `/Users/fydupre/Projects/ydj-music-studio/`
- ✅ Generated PLANNING.md with vision, strategy, and 5-phase roadmap
- **Next**: Migrate YDJ folder contents into organized structure

## Constraints and Conventions

### Safety Constraints
- **READ-ONLY Apple Music for now**: Use XML exports only; defer write operations to Phase 4
- **Always backup before bulk operations**: Apple Music library contains 10,000+ tracks
- **Test in isolation first**: Any AppleScript write operations must be tested on separate test library

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

### Critical Files (Existing in ~/Projects/YDJ/)
- `mixer.py` - 25KB, sophisticated simulated annealing optimizer
- `camelot.py` - 10KB, Camelot wheel implementation
- `cleanup.py` - Discrepancy detection across track variants
- `music_library.py` - Apple Music XML reader
- `rename_music_file.py` - File renaming based on tags
- Shell scripts in `ydj dl/` - Media processing pipeline
- `~/YDJ Library.xml` - Apple Music library export (user maintains separately)

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

### Apple Music Library Export
**Manual Process (for now):**
1. Open Apple Music → File → Library → Export Library
2. Save as `~/YDJ Library.xml`
3. Scripts read from this location

**Future:** Direct AppleScript integration (Phase 4)

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
cd ~/Projects/ydj-music-studio/mixer
python3 mixer.py
# Note: Currently uses hardcoded track list; will be enhanced in Phase 3
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

### External APIs (Future)
- MusicBrainz: Release dates, genres
- Discogs: DJ-focused metadata
- Spotify: Audio features, modern genres
- Last.fm: Genre tags, similar artists

## Next Actions

1. **Create genre taxonomy JSON**
   - Extract 31 genres from Apple Music XML
   - Save to `common/genres.json`
   - Format: simple array of strings

2. **Migrate YDJ folder contents**
   - Move `mixer.py`, `camelot.py` → `mixer/`
   - Move `cleanup.py`, `music_library.py`, `rename_music_file.py` → `library-management/`
   - Move shell scripts from `ydj dl/` → `downloads/`
   - Move CSV files → `data/`
   - Create venv in new location

3. **Create requirements.txt**
   - pandas, numpy, mutagen, fuzzywuzzy, python-Levenshtein
   - Test installation in fresh venv

4. **Initialize Git repository**
   - Create .gitignore (venv/, data/exports/, *.csv, *.xml, processed/)
   - Initial commit with migrated structure
   - Create GitHub repo and push

5. **Create subfolder README and CLAUDE.md files**
   - Document each subsystem's purpose and usage
   - Provide focused AI context for each domain

## Notes
- Existing YDJ folder at `~/Projects/YDJ/` will be renamed to `ydj-music-studio` after migration
- CSV files are legacy; will eventually be replaced by direct XML parsing
- Virtual environment in `path/to/venv/` is old; creating fresh one
- Keep shell scripts executable: `chmod +x downloads/*.sh`
