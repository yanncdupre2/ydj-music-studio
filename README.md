# YDJ Music Studio

**Status:** In Development (Phase 1: Foundation & Organization)

A comprehensive DJ music production and library management system for organizing, tagging, and optimizing music collections. Combines intelligent playlist optimization using harmonic mixing, automated metadata management for Apple Music libraries, and efficient media processing for YouTube-downloaded content.

## Overview

YDJ Music Studio addresses three core challenges for DJs:

1. **Playlist Optimization** - Create harmonically mixed sets using Camelot wheel system and BPM continuity via simulated annealing optimization
2. **Library Management** - Automated metadata tagging, cleanup, and LLM-powered genre categorization for Apple Music
3. **Media Processing** - Efficient batch conversion of YouTube downloads (MKV→MP4, Opus→AAC) for Apple ecosystem

## Key Features

### Mixer (Playlist Optimization)
- Harmonic mixing using Camelot wheel with ±1 semitone key shifting
- BPM continuity optimization with configurable thresholds
- Simulated annealing algorithm for optimal track ordering
- Future: Rust port for 10-100x performance improvement

### Library Management
- Canonical 31-genre taxonomy with compound categories (e.g., "EDM, House, Techno")
- Duplicate/discrepancy detection across track variants
- File renaming based on metadata tags
- Safe read-only XML workflow (AppleScript integration planned)

### Downloads Processing
- MKV classification (real video vs. static image)
- Lossless MKV→MP4 remuxing and VP9→H.264 transcoding
- Automatic 4K→1080p downscaling
- Opus→AAC audio conversion for Apple Music compatibility

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

### Run Mixer (Current - Hardcoded Playlist)
```bash
cd mixer
python3 mixer.py
```

### Process YouTube Downloads
```bash
cd downloads
./process_mkv.sh           # Classify videos
./convert_mkv_to_mp4.sh    # Lossless conversion
./reencode_all_mkv.sh      # Transcode incompatible codecs
```

## Project Structure

```
ydj-music-studio/
├── common/              # Shared utilities (Apple Music reader, genres taxonomy)
├── mixer/               # Playlist optimization (Camelot, simulated annealing)
├── library-management/  # Tagging, cleanup, file renaming
├── downloads/           # YouTube media processing (MKV/Opus conversion)
└── data/                # Working data (XML exports, CSVs)
```

Each subfolder contains its own `CLAUDE.md` for focused AI agent context and domain-specific README.

## Documentation

- **[PLANNING.md](PLANNING.md)** - Full project vision, strategy, and 5-phase roadmap
- **[PROJECT-LOCAL-CONTEXT.md](PROJECT-LOCAL-CONTEXT.md)** - Current execution context, architecture, and next actions
- **Subfolder READMEs** - Domain-specific documentation for mixer, library-management, downloads

## Development Status

**Current Phase:** Phase 1 - Foundation & Organization
- ✅ Project structure established
- ✅ Planning and context documentation complete
- 🔄 Migrating existing scripts from legacy YDJ folder
- 📋 Next: Extract genre taxonomy, set up Git repository

See [PLANNING.md](PLANNING.md) for full roadmap and [PROJECT-LOCAL-CONTEXT.md](PROJECT-LOCAL-CONTEXT.md) for immediate next actions.

## Technology Stack

- **Python 3.x** - pandas, numpy, mutagen, fuzzywuzzy
- **Bash/Shell** - ffmpeg-based media processing
- **Apple Music** - Library management via XML export (future: AppleScript)
- **Rust** - Future performance-critical mixer optimization engine

## License

Personal project for YDJ music production workflows.

## GitHub

https://github.com/fydupre/ydj-music-studio
