# Mixer - Playlist Optimization

Harmonic mixing and BPM continuity optimization using the Camelot wheel system and simulated annealing.

## Files

- **`mixer.py`** - Main optimization engine using simulated annealing algorithm
- **`camelot.py`** - Camelot wheel system implementation (key mapping, shifting, harmonic compatibility)
- **`playlist_manager.py`** - *(Future)* Dynamic playlist management from Apple Music

## How It Works

### Camelot Wheel System
The Camelot wheel maps musical keys to a 12-hour clock with A (minor) and B (major) designations:
- Same number = harmonically compatible (e.g., 8A → 8B)
- Adjacent numbers (±1) = smooth transitions (e.g., 8A → 7A or 9A)
- Key shifting (±1 semitone) expands transition possibilities

### Optimization Algorithm
Uses simulated annealing to find optimal track order that minimizes:
- **Harmonic cost**: Non-compatible key transitions
- **Tempo cost**: BPM jumps beyond threshold
- **Shift penalty**: Preference for original keys over shifted

### Current Limitations
- Hardcoded track list (manual editing required)
- Slow performance on large playlists (tens of minutes for 30 songs)
- No direct Apple Music playlist integration

## Usage

### Current (Hardcoded Playlist)
```bash
cd ~/Projects/ydj-music-studio/mixer
source ../venv/bin/activate
python3 mixer.py
```

Edit the `mix_tracks_list` array in `mixer.py` to change tracks.

### Future (Dynamic Playlists)
```bash
python3 mixer.py --playlist "My DJ Set"
```

## Output

The optimizer reports:
- Best track order with BPM, key (original + shift), and effective key
- Transition costs (harmonic and tempo) between consecutive tracks
- Tempo break candidates (suggestions for bridging large BPM gaps)
- Per-track aggregate transition costs across optimization attempts

## Configuration

Key parameters in `mixer.py`:
- `TEMPO_THRESHOLD = 4.5` - Maximum acceptable BPM difference
- `TEMPO_PENALTY = 5` - Cost for BPM jumps beyond threshold
- `EXACT_MATCH_COST = 0` - Perfect harmonic match
- `NON_HARMONIC_COST = 5` - Incompatible key transition
- `TOTAL_ITERATIONS = 410000` - Annealing iterations
- `ANNEALING_TRIES = 5` - Multiple optimization attempts

## Future Improvements

### Phase 3: Mixer Enhancements
- Dynamic playlist management (read from Apple Music)
- Export optimized playlist back to Apple Music
- Better visualization (flow charts, transition diagrams)
- Command-line interface with progress reporting

### Phase 5: Rust Port
- Port optimization core to Rust for 10-100x performance improvement
- Target: 30-song playlist in seconds vs. current tens of minutes
- Maintain Python wrapper for ease of use
