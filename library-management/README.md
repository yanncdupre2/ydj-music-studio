# Library Management - Metadata Tagging & Cleanup

Tools for organizing, tagging, and cleaning up Apple Music library metadata.

## Files

- **`cleanup.py`** - Interactive discrepancy detection and resolution for duplicate/similar tracks
- **`rename_files.py`** - Rename audio files based on metadata tags
- **`tag_updater.py`** - *(Future)* Batch metadata updates

## Features

### Discrepancy Detection (`cleanup.py`)

Identifies tracks with inconsistent metadata across variants:
- Same song (normalized title) by same artist/album artist
- Different year, genre, or rating values
- Presents groups interactively for manual review

**Usage:**
```bash
cd ~/Projects/ydj-music-studio/library-management
source ../venv/bin/activate
python3 cleanup.py
```

**What it does:**
1. Loads Apple Music library from `~/YDJ Library.xml`
2. Normalizes titles (removes accents, "(Video)", "(Remix)", etc.)
3. Groups by artist and normalized title
4. Finds groups with discrepant year/genre/rating
5. Displays interactively, sorted by most recent addition

**Example output:**
```
Grouping Artist: Madonna
Song Group: celebration
Most Recent Date Added: 2024-11-15
----------------------------------------
Name                        Year  Genre     Rating  Date Added
Celebration                 2009  Pop       80      2024-11-15
Celebration (Video)         2009  Pop       60      2023-05-20
Celebration (Extended Mix)  2009  Dance     80      2024-11-15
```

### File Renaming (`rename_files.py`)

Renames audio files (MP3, M4A, MP4, M4V) based on embedded metadata tags.

**Naming format:**
```
{AlbumArtist or Artist} - {Title} (Year) [Genre] [BPM, Key].ext
```

**Example:**
```
Before: track01.mp3
After:  Daft Punk - One More Time (2000) [EDM, House, Techno] [123 BPM, 5A].mp3
```

**Usage:**
```bash
cd ~/Projects/ydj-music-studio/library-management
python3 rename_files.py
# GUI folder picker appears
# Set DRY_RUN = False in script to actually rename
```

**Features:**
- Handles both ID3 (MP3) and MP4 atoms (M4A/MP4/M4V)
- Treats "Various Artists" aliases as fallback to track artist
- Extracts BPM and musical key from tags
- Configurable format (year/genre/BPM sections can be toggled)
- Dry-run mode for safety

## Genre Taxonomy

Uses canonical 31-genre taxonomy from `../common/genres.json`:
- Compound genres solve classification ambiguity (e.g., "EDM, House, Techno")
- Genres with 20+ songs in library
- Maintained for consistency across library

**Example genres:**
- "Pop"
- "Rock, Classic Rock"
- "Alternative, Indie, Grunge, Punk"
- "EDM, House, Techno"
- "New-Wave, Techno-Pop, Electro-Pop, Synth-Pop"

## Workflow

### 1. Export Apple Music Library
```bash
# In Apple Music:
# File → Library → Export Library
# Save as: ~/YDJ Library.xml
```

### 2. Find Discrepancies
```bash
python3 cleanup.py
# Review interactively, note tracks needing updates
```

### 3. Update Metadata in Apple Music
*Manual process for now (Phase 4 will add AppleScript automation)*

### 4. Re-export and Verify
```bash
# Export updated library
# Re-run cleanup.py to verify fixes
```

### 5. Rename Files (Optional)
```bash
python3 rename_files.py
# Select folder with audio files
# Review changes (DRY_RUN mode)
# Set DRY_RUN = False to apply
```

## Future Enhancements

### Phase 2: Library Management
- LLM-powered genre auto-tagging using canonical taxonomy
- Batch year lookup from MusicBrainz/Discogs APIs
- BPM detection for tracks missing tempo data
- Duplicate detection (similar tracks, different encodings)

### Phase 4: Safe Apple Music Write
- AppleScript integration for direct metadata updates
- Batch tag updates without manual intervention
- Validation and rollback capabilities
- Test library workflow before production use

## Configuration

### cleanup.py
- Library path: `~/YDJ Library.xml` (hardcoded in `common/apple_music.py`)
- Normalization: Removes accents, video tags, remix suffixes
- Grouping: By Album Artist (or Artist if empty)

### rename_files.py
- `DRY_RUN = True` - Set to `False` to actually rename files
- `FILENAME_PATTERN` - Customize output format
- `INCLUDE_YEAR_PARENS = True` - Include (Year)
- `INCLUDE_GENRE_BRACKETS = True` - Include [Genre]
- `INCLUDE_BPM_KEY_BRACKETS = True` - Include [BPM, Key]

## Safety Notes

- **Always backup Apple Music library before bulk operations**
- Use DRY_RUN mode first when renaming files
- cleanup.py is read-only (displays only, doesn't modify)
- Current workflow uses XML export (read-only) for safety
- Direct Apple Music write deferred to Phase 4 with extensive testing
