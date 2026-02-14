# Mixer - AI Agent Context

This subfolder focuses on **playlist optimization** using harmonic mixing and BPM continuity.

## Quick Context

**Purpose:** Optimize DJ playlist track order for seamless harmonic mixing and tempo flow

**Core Algorithm:** Simulated annealing optimization with Camelot wheel harmonic compatibility

**Current State:** Functional Python implementation, but slow (tens of minutes for 30-song playlist)

## Key Files

- `mixer.py` - Simulated annealing optimizer (613 lines)
- `camelot.py` - Camelot wheel system (295 lines)
- Imports `common/apple_music.py` for library loading

## Architecture

### Optimization Approach
1. Load track metadata from Apple Music XML export
2. Extract BPM and Camelot key (stored in Comments field)
3. Try random track orderings with key shifts (-1, 0, +1 semitones)
4. Score each ordering: harmonic cost + tempo cost + shift penalty
5. Accept better solutions; occasionally accept worse (simulated annealing)
6. Report best ordering after multiple attempts

### Cost Function
- Harmonic: Based on Camelot wheel compatibility (0 = perfect, 5 = dissonant)
- Tempo: Penalty for BPM jumps beyond threshold (default: 4.5 BPM)
- Shift: Small penalty for using shifted keys vs. original

### Camelot Wheel
- 12 positions (like clock: 1-12)
- Two modes per position: A (minor), B (major)
- Compatible transitions: same number, ±1 number, A↔B at same number

## Current Limitations

1. **Hardcoded playlist** - Track list is manually edited in `mixer.py` (lines 136-152)
2. **Performance** - Python implementation is slow; considers Rust port for future
3. **No Apple Music integration** - Can't read/write playlists directly
4. **Library path** - Expects `~/YDJ Library.xml` (hardcoded in `common/apple_music.py`)

## Execution Constraints

- **Do NOT modify camelot.py** unless fixing bugs - well-tested harmonic logic
- **Performance optimization** - Acceptable to enhance mixer.py algorithm, but major speed gains require Rust (Phase 5)
- **Track list format** - If helping add tracks, maintain tuple format: `("Title", "Artist")`
- **Key extraction** - Keys must be in Comments field of Apple Music tracks (e.g., "5A" for A-minor at position 5)

## Common Tasks

### Adding tracks to mix
Edit `mix_tracks_list` array in `mixer.py` (lines 136-152):
```python
mix_tracks_list = [
    ("Song Title", "Artist Name"),
    ...
]
```

### Adjusting optimization parameters
Edit global parameters at top of `mixer.py` (lines 18-42)

### Understanding output
- Each track shows: position, BPM, original key [shift], effective key, transition costs
- Harmonic cost (H): 0 = perfect, 0.5-1 = good, 5+ = bad
- Tempo cost (T): 0 = within threshold, 5+ = tempo break

## Future Development

**Phase 3 priorities:**
1. Dynamic playlist management (not hardcoded arrays)
2. Read Apple Music playlists by name
3. Export optimized playlist back to Apple Music
4. Visual flow chart of transitions

**Phase 5: Rust port**
- 10-100x performance improvement target
- Keep Python wrapper for integration
- Focus on optimization loop, not I/O

## Related Files

- `../common/apple_music.py` - Loads library from XML export
- `../common/genres.json` - Not used by mixer, but part of library management
- `../PLANNING.md` - Full project vision and roadmap
- `../PROJECT-LOCAL-CONTEXT.md` - Overall project context

When working on mixer code, focus on this subfolder. For library management tasks, work in `../library-management/`.
