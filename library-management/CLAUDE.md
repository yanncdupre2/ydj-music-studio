# Library Management - AI Agent Context

This subfolder focuses on **metadata tagging, cleanup, and organization** for Apple Music library.

## Quick Context

**Purpose:** Maintain consistent, accurate metadata across the DJ library — 8,622 tracks inside a 20,330-track Apple Music library

**Current Approach:** Live AppleScript reads; live writes through gated tools only (year/genre
taggers, artist spelling cleanup). `PLANNING.md` "Architecture Decisions" governs write safety
and overrides anything older here.

## Key Files

- `cleanup.py` - Discrepancy detection for duplicate/similar tracks
- `rename_files.py` - File renaming based on metadata tags
- `tag_tracks.py` / `resolve_tagger.py` - Year/genre writes, one keypress per track
- `artist_spellings.py` - One spelling per artist (scan / review / apply / undo); see README
- Imports `common/apple_music.py` for library loading

## Architecture

### Data Flow (Current)
1. User exports Apple Music library → `~/YDJ Library.xml`
2. Scripts load XML using `common/apple_music.py`
3. Analysis identifies discrepancies or generates new filenames
4. User manually updates Apple Music library
5. User re-exports to verify changes

### Genre Taxonomy (Critical)
- **31 canonical compound genres** stored in `../common/genres.json`
- Examples: "EDM, House, Techno", "New-Wave, Techno-Pop, Electro-Pop, Synth-Pop"
- **Philosophy:** Compound genres solve "is it House or Techno?" ambiguity
- Only tracks whose genre is outside this list need reclassifying. A canonical
  genre may legitimately be small in the DJ subset (`Classical, Lyrical`: 5 DJ
  tracks, 1,459 library-wide)

### Metadata Fields
**Priority fields:**
- Year - Release year (4-digit)
- Genre - From canonical 31-genre list
- BPM - Tempo for DJ mixing
- Key - Camelot notation (e.g., "5A") stored in Comments field

**Secondary fields:**
- Rating - 0-100 scale
- Album Artist - Preferred over Artist for grouping
- Comments - Contains Camelot key

## Current Limitations

1. **Subscription tracks can't be written** by script (see `PROJECT-LOCAL-CONTEXT.md`)
2. **XML dependency** - `cleanup.py` still reads the manual XML export
3. **BPM / Comments** are not written by this repo, by decision: Mixed In Key
   writes BPM and the key (`07A - Energy 7`). Tracks lacking them need an MIK
   pass, not new tooling (`PLANNING.md`, Architecture Decisions)

## Execution Constraints

### Safety First
- Write to the library only through the gated tools above, never ad hoc
- Back up first: `venv/bin/python common/library_backup.py backup --note "before X"`
- A separate test library is not required (`PLANNING.md`: no workflow deletes a track)
- Renaming an artist/album moves files ("Keep Music Media folder organized" is on);
  VirtualDJ then shows them as new songs without cue points. Accepted; **never edit
  VirtualDJ's files** (`database.xml`, lists) to compensate

### Genre Taxonomy Rules
- **Use exact genre strings** from `../common/genres.json`
- Do NOT create single-genre classifications (violates compound philosophy)
- If suggesting genre for a track, pick from canonical 31 genres
- When in doubt, use broader compound category (e.g., "EDM, House, Techno" over specific subgenre)

### File Operations
- rename_files.py operates on audio files, NOT Apple Music library
- Always check DRY_RUN setting before running rename operations
- Preserve original files (don't overwrite without confirmation)

## Common Tasks

### Run discrepancy detection
```bash
python3 cleanup.py
# Displays groups interactively
# User presses Enter to advance
```

### Analyze specific issue
Help user understand why cleanup.py flagged a track group:
- Check normalization logic (accents, video tags removed)
- Explain grouping by Album Artist vs Artist
- Identify which metadata field is inconsistent

### Suggest genre updates
When user asks "what genre should this be?":
1. Check if artist/song already in library (load XML)
2. Look at similar tracks by same artist
3. Recommend from canonical 31 genres in `../common/genres.json`
4. Prefer compound genres over single categories

### File renaming assistance
- Review FILENAME_PATTERN configuration
- Explain DRY_RUN mode
- Help troubleshoot missing metadata (check ID3/MP4 tags)

## Future Development

**Phase 2 priorities (current focus after migration):**
1. Audit library metadata completeness (% missing year, genre, BPM)
2. Enhance cleanup.py with better interactive workflow
3. LLM-powered genre auto-tagging using canonical taxonomy
4. Batch year lookup from MusicBrainz/Discogs

**Phase 4: Safe write operations**
1. Research AppleScript capabilities for Apple Music
2. Create isolated test library (separate from production)
3. Implement write operations with validation
4. Extensive testing before touching production library

## Related Files

- `../common/apple_music.py` - XML library reader
- `../common/genres.json` - Canonical 31-genre taxonomy
- `../PLANNING.md` - Full project vision and phases
- `../PROJECT-LOCAL-CONTEXT.md` - Overall project context

## Integration Points

- **Mixer** uses BPM and Key (from Comments) for optimization
- **Downloads** produces files that need tagging and import to library
- **Common** provides shared Apple Music library access

When working on library management, focus on consistency, safety, and the canonical genre taxonomy. Library writes follow the gating, backup and undo rules in `PLANNING.md`.
