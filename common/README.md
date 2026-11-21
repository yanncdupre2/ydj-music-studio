# Common - Shared Utilities

Shared utilities and resources used across mixer, library-management, and downloads subprojects.

## Files

- **`apple_music.py`** - Apple Music library XML parser
- **`library_backup.py`** - Back up / restore the Apple Music library database (see below)
- **`genres.json`** - Canonical 31-genre taxonomy
- **`metadata_utils.py`** - *(Future)* Common metadata operations

## Apple Music Library Reader

### `apple_music.py`

Loads Apple Music library from XML export and returns pandas DataFrame.

**Usage:**
```python
from common.apple_music import load_library

df = load_library()
# Returns DataFrame with columns:
# - Track ID, Name, Artist, Album, Album Artist
# - Genre, Grouping, Comments, Year, Rating
# - BPM, Play Count, Skip Count
# - Date Added, Last Played, etc.
```

**Configuration:**
- Library path: `~/YDJ Library.xml` (hardcoded)
- Uses plistlib to parse Apple Music PropertyList XML

**Export Apple Music Library:**
1. Open Apple Music
2. File → Library → Export Library
3. Save as `~/YDJ Library.xml`

## Genre Taxonomy

### `genres.json`

Canonical list of 31 compound genres used for consistent tagging across library.

**Philosophy:**
- Compound genres solve classification ambiguity (e.g., "EDM, House, Techno")
- Allows tracks to belong to multiple related genres simultaneously
- Example: "New-Wave, Techno-Pop, Electro-Pop, Synth-Pop" covers similar 80s electronic styles

**Selection Criteria:**
- Genres with 20+ songs in library
- Covers ~95% of library tracks
- A canonical genre can still be small within a given playlist subset; small is
  not the same as off-taxonomy. Only genre strings outside this list need
  reclassifying (measured 2026-09-19: 2 such strings across the DJ library)

**Usage:**
```python
import json

with open('common/genres.json', 'r') as f:
    canonical_genres = json.load(f)

# Use for LLM prompts:
# "Categorize this song using ONLY these genres: {canonical_genres}"
```

## Genre List (31 Total)

1. Pop
2. Rock, Classic Rock
3. Alternative, Indie, Grunge, Punk
4. French
5. Classical, Lyrical
6. EDM, House, Techno
7. New-Wave, Techno-Pop, Electro-Pop, Synth-Pop
8. Soundtrack
9. Children
10. Hard Rock, Heavy Metal
11. Hip-Hop/Rap
12. Dance, Disco, R&B, Soul, Funk
13. Jazz, Blues, Swing
14. Holiday
15. Brazilian
16. Chill
17. Trance
18. Recordings
19. New Age
20. Electronic, Ambient, Experimental
21. Latin
22. Comedy
23. Country
24. World
25. Books & Spoken
26. Dance
27. Reggae, Caribbean
28. African, Arabic, Israeli, Indian, Islander
29. Dubstep
30. Slow
31. Dark Wave, Goth

## Integration Points

### Mixer
- Uses `load_library()` to get track metadata (BPM, key)
- Extracts Camelot key from Comments field

### Library Management
- Uses `load_library()` for discrepancy detection
- References `genres.json` for genre validation and LLM prompts

### Future: Metadata Utils

Planned `metadata_utils.py` for shared operations:
- Normalize text (remove accents, special chars)
- Parse dates, durations, ratings
- Convert between different key notations (Camelot, pitch class, Open Key)
- Common fuzzy matching utilities

## Dependencies

- **pandas** - DataFrame operations
- **plistlib** - Built-in Python XML parser for Apple Music format
- **unicodedata** - Accent removal and text normalization

## Library Backup (`library_backup.py`)

Take one before any script writes to the library in bulk:

```bash
venv/bin/python common/library_backup.py backup --note "before artist cleanup"
venv/bin/python common/library_backup.py list
venv/bin/python common/library_backup.py restore NAME   # then: quit Music, Option-launch it,
                                                        # Choose Library, pick the prepared package
venv/bin/python common/library_backup.py check          # which library Music uses now
```

- **Backup** clones `Music Library.musiclibrary` (~0.5 GB; APFS clones cost no
  space until the library changes) into `~/Music/Music/YDJ Library Backups/<date time>/`,
  without quitting Music. It is kept only if the library's files are identical before
  and after the copy; `manifest.json` holds every file's SHA-256 and when the library
  was last saved, which is what the backup contains.
- **Restore** checks the backup against its manifest and clones it next to the
  library as `Music Library [restored NAME].musiclibrary`. You switch Music to it
  with Option-launch → Choose Library. The current library is never touched, so
  switching back is the undo.
- **Why not simply copy files back:** the library is held by a background process,
  AMPLibraryAgent, which outlives Music, saves only now and then, and writes its copy
  back over replaced files. It can't be stopped safely from a script (SIGTERM can
  lose unsaved changes). Details in `PLANNING.md`, "Library backup".
- Not covered: media files (outside the package). With iCloud Sync Library on, Music
  may re-apply cloud changes after switching to an older library.

## Safety Notes

- **`apple_music.py` / `load_from_music_app.py`** read the library (XML export or
  live AppleScript). Year/genre writes live in the library-management taggers, which
  gate every write with a keypress.
- **Back up first** with `library_backup.py` before any bulk write.
