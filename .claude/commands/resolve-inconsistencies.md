Resolve year/genre inconsistencies across track variants (audio, video, extended, remix).

## Workflow

You are working in the `ydj-music-studio` project. The library management scripts live in `library-management/`.

### Step 1: Detect inconsistency groups and research (ONE command)
Run `resolve_inconsistencies.py` to scan DJ playlists for groups with conflicting metadata:
```bash
cd /Users/fydupre/Projects/ydj-music-studio/library-management && python3 resolve_inconsistencies.py --output /tmp/inconsistency_groups.json
```
This detects groups, filters out already-ignored tracks, and queries Source A (group majority) and Source D (MusicBrainz) for each group.

### Step 2: Fill in Source B + Source C
Read `/tmp/inconsistency_groups.json`. For each group where source_b and source_c are empty:
- **Source B (LLM knowledge):** Use your own knowledge to fill in `source_b.year` and `source_b.genre` (use a genre string like "pop", "rock", "french pop", "edm", etc.)
- **Source C (Web search):** Do a web search for "{artist} {title} genre year" and fill in `source_c.year` and `source_c.genre`

After filling in all sources, recompute the `consensus` field for each group using `determine_consensus()` logic:
- Year: most common year across sources
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
- The 31 valid YDJ genres are in `common/genres.json` — always map to one of those
- Strip "(Video)" / "(Lyric Video)" from titles before web searching
- MusicBrainz rate limit is 1 req/sec (already handled in the script)
- Groups already in the "Ignore year or genre inconsistencies" playlist are filtered out automatically
- Source A is the majority year/genre from the group's own tracks (not a library search)
- If no inconsistency groups are found, inform the user that all track variants have consistent metadata
