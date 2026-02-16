Resolve year/genre inconsistencies across track variants (audio, video, extended, remix).

## Workflow

You are working in the `ydj-music-studio` project. The library management scripts live in `library-management/`.

### Step 1: Detect inconsistency groups and research (ONE command)
Run `resolve_inconsistencies.py` to scan the "DJ AUDIO + VIDEO" playlist in Apple Music for groups with conflicting metadata:
```bash
cd /Users/fydupre/Projects/ydj-music-studio/library-management && python3 resolve_inconsistencies.py --output /tmp/inconsistency_groups.json
```
This reads tracks **directly from Apple Music via AppleScript** (no XML export needed), detects groups, filters out already-ignored tracks, and queries Source A (group majority) and Source D (MusicBrainz) for each group.

To analyze a specific playlist instead:
```bash
cd /Users/fydupre/Projects/ydj-music-studio/library-management && python3 resolve_inconsistencies.py --playlist "Playlist Name" --output /tmp/inconsistency_groups.json
```

### Step 2: Fill in Source B (LLM knowledge only — no web searches)
Read `/tmp/inconsistency_groups.json`. For each group where source_b is empty:
- **Source B (LLM knowledge):** Use your own knowledge to fill in `source_b.year` and `source_b.genre` (use a genre string like "pop", "rock", "french pop", "edm", etc.)
- **Source C: SKIP** — do NOT use web searches (they consume session limits too fast). Leave source_c empty.

After filling in Source B, recompute the `consensus` field for each group using `determine_consensus()` logic:
- Year: most common year across sources (prefer original release year, not reissues)
- Genre: map all source genres through `map_genre_to_ydj()`, pick the most common as primary, second-most as alternate
- Confidence: high (3+ agree), medium (2 agree), low (1 or none)

Write the updated JSON back to `/tmp/inconsistency_groups.json`.

### Step 3: Interactive resolution (requires real terminal)
The resolver needs interactive keypress input, so open it in a **new Terminal window**:
```bash
osascript -e 'tell application "Terminal"
    activate
    do script "cd /Users/fydupre/Projects/ydj-music-studio && ./run-resolver.sh"
end tell'
```
Tell the user: a Terminal window has opened. For each inconsistency group, press:
- **1** = Fix all tracks with primary genre + consensus year
- **2** = Fix all tracks with alternate genre + consensus year
- **I** = Ignore (add tracks to "Ignore year or genre inconsistencies" playlist)
- **S** = Skip
- **Q** = Quit

## Important notes
- **NO XML EXPORT NEEDED** — all track data is read directly from Apple Music via AppleScript
- **Track verification**: Before any update, the resolver verifies each track's database ID still matches the expected artist + name. Mismatches are skipped with an error message.
- The 31 valid YDJ genres are in `common/genres.json` — always map to one of those
- Strip "(Video)" / "(Lyric Video)" / "(Extended Mix)" etc. from titles before MusicBrainz/LLM lookups
- MusicBrainz rate limit is 1 req/sec (already handled in the script)
- MusicBrainz often returns reissue/compilation years — prefer original release year from LLM knowledge
- Groups already in the "Ignore year or genre inconsistencies" playlist are filtered out automatically
- Source A is the majority year/genre from the group's own tracks (not a library search)
- If no inconsistency groups are found, inform the user that all track variants have consistent metadata
