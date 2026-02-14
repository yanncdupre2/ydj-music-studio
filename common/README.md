# Common - Shared Utilities

Shared utilities and resources used across mixer, library-management, and downloads subprojects.

## Files

- **`apple_music.py`** - Apple Music library XML parser
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
- Smaller genres (<20 songs) will be reclassified using this taxonomy

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

## Safety Notes

- **Read-only operations** - This module only reads Apple Music XML export
- **No write operations** - Cannot modify Apple Music library (by design, for safety)
- **Manual export required** - User must export XML manually from Apple Music
- Future AppleScript integration (Phase 4) will enable direct library access
