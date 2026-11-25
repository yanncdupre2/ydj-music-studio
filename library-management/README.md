# Library Management - Metadata Tagging & Cleanup

Tools for organizing, tagging, and cleaning up Apple Music library metadata.

## Files

- **`cleanup.py`** - Interactive discrepancy detection and resolution for duplicate/similar tracks
- **`rename_files.py`** - Rename audio files based on metadata tags
- **`artist_spellings.py`** - Make each artist's name consistent (Artist + Album Artist)
- **`tag_updater.py`** - *(Future)* Batch metadata updates

## Features

### Artist Spelling Cleanup (`artist_spellings.py`)

The library spelled some artists several ways ("Mc Solaar" / "MC Solaar",
"Tiesto" / "Tiësto"). This finds them across Artist and Album Artist, lets you
pick one spelling per artist, and writes it.

```bash
venv/bin/python library-management/artist_spellings.py scan       # read-only: groups + MusicBrainz names
venv/bin/python library-management/artist_spellings.py review     # in Terminal.app: one keypress per artist
venv/bin/python library-management/artist_spellings.py apply --dry-run
venv/bin/python library-management/artist_spellings.py apply      # backs up the library first
venv/bin/python library-management/artist_spellings.py undo       # put the old values back
```

- **scan** groups spellings that differ only by case, accents, spacing, Unicode
  encoding or typographic punctuation, and asks MusicBrainz for each group's
  spelling (cached in `data/musicbrainz_artists.json`; a 503 is MusicBrainz
  rate limiting, retried, and an unfinished lookup is retried on the next scan).
- **review** shows each spelling with its Artist / Album Artist counts, plus
  MusicBrainz's and an accent-free one, and how many files each choice would
  move. Decisions are saved as you go (`data/artist_decisions.json`); quit and
  resume any time. Needs a real terminal (raw keypresses).
- **apply** takes a library backup (`common/library_backup.py`), then per track
  checks the current value, journals the change with the file's path before and
  after (`data/artist_journal.jsonl`), writes, and reads back. Apple Music
  subscription tracks can't be written by script and are listed to fix by hand.
  `--only ARTIST ...` limits it to some artists (trial runs).
- **Files move** when "Keep Music Media folder organized" is on (it is) and the
  name the folder is built from changes: Album Artist if set, else Artist;
  compilation albums stay in `Compilations`. Measured in the 2026-11-21 trial:
  a case-only change (`Mc Solaar` → `MC Solaar`) moved nothing, Music only
  re-cased the stored path; an accent change (`Claude Francois` → `Claude
  François`) moved the file and removed the old folder.
- **VirtualDJ** keys its database (cue points, BPM/key scan) by file path, so it
  shows a moved file as a new song without its cues. That is accepted: cues get
  re-checked before each party anyway. The journal's `path_before` / `path_after`
  tell which files moved. Do not edit VirtualDJ's `database.xml` or lists from a
  script: see "Artist spelling cleanup" in `PLANNING.md` for what that did.
- **undo** restores journaled values newest first.

First run (2026-11-21): 81 artists decided, 714 tracks changed, 89 files moved
(13 artists, all accent changes), 1 subscription track to fix by hand. Björk
was switched from "Bjork" to "Björk" on 2026-11-22 (15 files moved).

Music refused 23 tracks with "File permission error (-54)". All are cloud-only
entries (class `shared track`, cloud status `unknown`) that duplicate a local
file by the same artist, which was fixed (22 of 23 the same length to 0.1 s).
Music also refuses to download them by script ("Parameter error (-50)").

Cloud-only duplicates (2026-11-22): of 711 cloud-only tracks, 151 duplicate a
downloaded track (same artist and title by group key, same length within 1 s,
file on disk). Before deletion, the downloaded copy was added to the ordinary
playlists only its cloud copy was in (22 additions, appended at the end) and
given the cloud copy's higher stars (7 tracks); log with old values in
`data/cloud_duplicates_fixes.jsonl`. The 151 are collected in the Music
playlist "Cloud duplicates to delete" for deletion by hand (the scripts never
delete tracks). 22 more share a title but differ in length, so they are
probably other versions and were left alone.

VirtualDJ observation (2026-11-21): when VirtualDJ first saw two moved Björk
videos, their new entries already had cue points (8 and 1). Most likely
VirtualDJ read them from the cue tags Mixed In Key writes into the files (not
checked), so a move may cost fewer cues than feared.

Consent is per artist (one keypress in review settles all its tracks), not per
track as in the taggers; the backup and journal are the safety net (see
`PLANNING.md`).

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

- **Always back up the Apple Music library before bulk operations**: `common/library_backup.py backup`
- Use DRY_RUN mode first when renaming files
- cleanup.py is read-only (displays only, doesn't modify)
- Live writes: year/genre via the taggers (keypress per track), artist names via
  `artist_spellings.py` (keypress per artist, backup + journal + undo)
