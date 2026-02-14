Fill in missing genre and year metadata for tracks in the Apple Music library.

## Workflow

You are working in the `ydj-music-studio` project. The library management scripts live in `library-management/`.

### Step 1: Research automated sources (ONE command)
Run `research_tracks.py` reading directly from the smart playlist "Genre of Year Blank":
```bash
cd /Users/fydupre/Projects/ydj-music-studio/library-management && python3 research_tracks.py --playlist "Genre of Year Blank" --output /tmp/recommendations.json
```
This queries Source A (duplicates in Apple Music) and Source D (MusicBrainz) for every track.

### Step 2: Fill in Source B + Source C
Read `/tmp/recommendations.json`. For each track where source_b and source_c are empty:
- **Source B (LLM knowledge):** Use your own knowledge to fill in `source_b.year` and `source_b.genre` (use a genre string like "pop", "rock", "french pop", "edm", etc.)
- **Source C (Web search):** Do a web search for "{artist} {title} genre year" and fill in `source_c.year` and `source_c.genre`

After filling in all sources, recompute the `consensus` field for each track using `determine_consensus()` logic:
- Year: most common year across sources
- Genre: map all source genres through `map_genre_to_ydj()`, pick the most common as primary, second-most as alternate
- Confidence: high (3+ agree), medium (2 agree), low (1 or none)

Write the updated JSON back to `/tmp/recommendations.json`.

### Step 3: Interactive tagging (ONE command)
Run the interactive tagger:
```bash
cd /Users/fydupre/Projects/ydj-music-studio/library-management && python3 tag_tracks.py --input /tmp/recommendations.json
```
The user presses 1 (primary genre), 2 (alternate genre), or S (skip) for each track. No additional confirmations needed.

## Important notes
- The 31 valid YDJ genres are in `common/genres.json` — always map to one of those
- Strip "(Video)" / "(Lyric Video)" from titles before web searching
- MusicBrainz rate limit is 1 req/sec (already handled in the script)
- If the playlist is empty, inform the user that all tracks already have genre and year set
