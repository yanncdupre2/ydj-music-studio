# YDJ Music Studio

**Status:** In Progress — Phases 1, 4, and 5 complete; Phases 2 and 3 ongoing.

A comprehensive DJ music production and library management system for organizing, tagging, and optimizing music collections. Combines intelligent playlist optimization (with a Rust SA + Held-Karp engine), automated metadata management for Apple Music libraries, YouTube media processing, and karaoke video preparation for FCP overlay blending.

## Overview

YDJ Music Studio addresses four core workflows for DJs:

1. **Playlist Optimization** — Harmonic mixing via Camelot wheel + BPM continuity. Rust engine combines simulated annealing (60x throughput vs. Python) with Held-Karp exact DP for n ≤ 20 (provably optimal in seconds).
2. **Library Management** — Live AppleScript reads/writes, LLM-powered genre tagging from a canonical 31-genre taxonomy, interactive duplicate/inconsistency resolution.
3. **YouTube Media Processing** — yt-dlp downloads → rename to `Artist - Title (Video/Karaoke/Lyrics Video)` format using a live Apple Music artist list, MKV→MP4 conversion, Opus→AAC.
4. **Karaoke Video Prep** — Luminance-LUT pipeline turning a karaoke YouTube video into a black/white/sung-color overlay layer for Final Cut Pro `screen`/`add` blending. Optional `--no-lut` mode preserves multi-color text on a black background. Intro/outro preserve-or-blackout, zoom in/out, inverted-band polarity, outline halo, background darken, and a SwiftUI front-end.

## Key Features

### Mixer (Playlist Optimization)
- Harmonic mixing using Camelot wheel with ±1 semitone key shifting
- BPM continuity optimization with configurable thresholds
- Rust SA engine via PyO3 (60x throughput; ~3,500 attempts in 5 min)
- Held-Karp exact DP optimizer for n ≤ 20 tracks (global optimum guaranteed, < 5s)
- Reads "Mixer input" Apple Music playlist directly via AppleScript (no XML hardcoding)
- Bridge key/BPM hints rendered as `>>` rows between tracks for high-cost transitions

### Library Management
- Canonical 31-genre taxonomy with compound categories (e.g., "EDM, House, Techno")
- 4-source consensus tagging (duplicates / LLM knowledge / web search / MusicBrainz)
- Live AppleScript writes for year + genre (no XML refresh dependency)
- Interactive single-keypress tagger (`tag_tracks.py`) and inconsistency resolver (`resolve_tagger.py`)
- `/fill-missing-genres-years` and `/resolve-inconsistencies` slash commands

### Downloads Processing
- yt-dlp configured for h264/1080p with Safari cookies for YouTube Premium
- `rename_youtube.py` normalizes downloads using a live Apple Music artist list (~5s for 3,700 artists, no CSV/XML staleness)
- MKV classification (real video vs. static image)
- Lossless MKV→MP4 remuxing and VP9→H.264 transcoding
- Automatic 4K→1080p downscaling; Opus→AAC for Apple compatibility

### Karaoke Video Processing (`karaoke-process`)
- Luminance-LUT pipeline: grayscale → 3-band mapping (`< lo` → black, mid → white, `≥ hi` → sung-color) for clean FCP overlay blending
- `--no-lut` opt-out preserves the original multi-color text (per-singer colors in duets) on a black background; uses `-lo` as a floor-to-black threshold
- Configurable edge masking (full strips or `--corners-only`) to hide channel logos/watermarks
- Independent intro/outro segments (`--intro-preserve`, `--intro-blackout`, `--outro-preserve`, `--outro-blackout`)
- `-z N%` — uniform centered zoom (positive scales up + crops; negative scales down + center-pads with black for channels where lyrics sit too close to the edges)
- `--invert-bands` — swap mid/high LUT outputs (rescues channels where unsung is brighter than sung, e.g. Party Tyme)
- `--outline N` — high-contrast two-ring gray halo (default 2; 0 disables) for readability over busy backgrounds
- `--bg-color HEX` (+ `--bg-strength`, `--bg-range`, `--bg-blend`) — background darken for Karafun-style colored backgrounds
- `--sung-color HEX` — customize the sung-text color (default green `00C800`)
- Still-frame mode (`-f SECONDS`) for fast threshold/mask tuning
- SwiftUI GUI front-end (`KaraokeProcessGUI.app`) with live previews, persisted presets, foreground progress bar, and Finder Quick Action wrapper

## Quick Start

### Prerequisites
- macOS with Apple Music
- Python 3.x
- ffmpeg/ffprobe (install via `brew install ffmpeg`)

### Setup
```bash
cd ~/Projects/ydj-music-studio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Export Apple Music Library
1. Open Apple Music → File → Library → Export Library
2. Save as `~/YDJ Library.xml`

### Run Mixer
```bash
./run-mixer.sh                  # uses Rust engine (built once via maturin) with Python fallback
```

### Build Rust Mixer Engine (one-time after clone)
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
source venv/bin/activate
pip install maturin
cd src/ydj_mixer_engine && maturin develop --release
```

### Process YouTube Downloads
```bash
yt-dlp "https://www.youtube.com/watch?v=..."   # uses ~/.config/yt-dlp/config
python3 downloads/rename_youtube.py            # dry-run rename (live Apple Music artist list)
python3 downloads/rename_youtube.py --apply    # actually rename
```

### Karaoke Video Processing
```bash
karaoke-process "/path/to/karaoke.mp4"                                      # defaults
karaoke-process "/path/to/karaoke.mp4" -lo 40 -hi 200 --invert-bands -z 10  # Party Tyme polarity
karaoke-process "/path/to/karaoke.mp4" --no-lut -lo 50 --outline 2          # multi-color duet, lyrics on black
karaoke-process "/path/to/karaoke.mp4" --bg-color 4742B8 --bg-strength 95   # Karafun-style colored bg
```

See `karaoke-processing/karaoke-process.md` for the full reference (channel-specific starting points, tuning workflow, all options).

## Project Structure

```
ydj-music-studio/
├── common/              # Shared utilities (Apple Music reader, genres taxonomy)
├── mixer/               # Playlist optimization (Camelot, SA, planning docs)
├── library-management/  # Tagging, cleanup, inconsistency resolver
├── downloads/           # YouTube media processing (rename, MKV/Opus conversion)
├── karaoke-processing/  # karaoke-process script + SwiftUI GUI + reference doc
├── src/ydj_mixer_engine/# Rust SA + Held-Karp engine (PyO3/maturin)
└── data/                # Working data (XML exports, CSVs)
```

Each subfolder contains its own `CLAUDE.md` for focused AI agent context and domain-specific README.

## Documentation

- **[PLANNING.md](PLANNING.md)** - Full project vision, strategy, and 5-phase roadmap
- **[PROJECT-LOCAL-CONTEXT.md](PROJECT-LOCAL-CONTEXT.md)** - Current execution context, architecture, and next actions
- **Subfolder READMEs** - Domain-specific documentation for mixer, library-management, downloads

## Development Status

- ✅ **Phase 1** — Foundation & organization (modular structure, genres taxonomy, Git/GitHub)
- 🚧 **Phase 2** — Library management (tagging + inconsistency resolution shipping; BPM/key auditing pending)
- 🚧 **Phase 3** — Mixer enhancements (live AppleScript playlist input, bridge hints; export-back-to-Apple-Music pending)
- ✅ **Phase 4** — Safe AppleScript writes for year + genre (validated; in production use)
- ✅ **Phase 5** — Rust performance engine (60x SA throughput, Held-Karp exact for n ≤ 20)

Karaoke processing (cross-cutting): single canonical `karaoke-process` script in production at `~/.local/bin/karaoke-process` with SwiftUI front-end at `/Applications/KaraokeProcessGUI.app`.

See [PLANNING.md](PLANNING.md) for full roadmap and [PROJECT-LOCAL-CONTEXT.md](PROJECT-LOCAL-CONTEXT.md) for immediate next actions.

## Technology Stack

- **Python 3.x** — pandas, numpy, mutagen, fuzzywuzzy
- **Rust + PyO3 + maturin** — mixer SA + Held-Karp optimizer (`src/ydj_mixer_engine/`)
- **Bash + ffmpeg** — media processing (downloads, karaoke-process)
- **AppleScript** — live Apple Music reads + writes (year, genre, playlists)
- **MusicBrainz API** — release dates and genre lookups for missing metadata

## License

Personal project for YDJ music production workflows.

## GitHub

https://github.com/yanncdupre2/ydj-music-studio
