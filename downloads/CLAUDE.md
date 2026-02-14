# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a video/audio media processing workspace for downloaded content (primarily from YouTube/web sources). The scripts automate the conversion and organization of MKV video files and Opus audio files into Apple ecosystem-compatible formats (MP4/M4A).

## Architecture Overview

### Processing Pipeline

The repository implements a multi-stage media processing pipeline:

1. **MKV Classification** (`process_mkv.sh`)
   - Analyzes MKV files to distinguish between real videos and static image videos
   - Uses frame sampling at 10%, 50%, and 90% of duration
   - Compares frame similarity (threshold: 5% difference)
   - Static images: extracts audio stream, deletes MKV
   - Real videos: renames with "(Video)" suffix

2. **Lossless Remuxing** (`convert_mkv_to_mp4.sh`)
   - Fast container conversion (MKV → MP4) without re-encoding
   - Only processes files with H.264/H.265 video + AAC audio
   - Uses `-c copy` for bit-perfect stream copy
   - Incompatible codecs (VP9, Opus) are skipped

3. **Transcoding** (`reencode_all_mkv.sh`, `reencode_mkv_to_mp4.sh`)
   - Re-encodes incompatible codecs (VP9 → H.264, Opus → AAC)
   - Dynamic CRF selection based on file size:
     - Files < 50MB: CRF 21 (higher quality)
     - Files ≥ 50MB: CRF 22 (smaller size)
   - Automatically downscales 4K content to 1080p maximum
   - AAC audio at 192kbps

4. **Audio Conversion** (`convert_opus_to_aac.sh`)
   - Converts Opus audio files to M4A (AAC) format
   - AAC 192kbps for Apple ecosystem compatibility

### File Organization

- **Working directory**: Contains active media files being processed
- **processed/ folder**: Archive for original files after successful conversion
- All scripts move originals to `processed/` rather than deleting them

## Key Technical Details

### FFmpeg Usage Patterns

**Codec Detection:**
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$file"
```

**Resolution Detection:**
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,stream=height
```

**Quality Settings:**
- Video: H.264 with CRF 21-22, medium preset
- Audio: AAC 192kbps
- Container: MP4/M4A with `+faststart` flag for streaming optimization

**4K Downscaling:**
```bash
scale='min(1920,iw)':'min(1080,ih)':force_original_aspect_ratio=decrease
```

### Script Execution Pattern

All scripts follow this pattern:
1. Process files matching pattern (`*.mkv`, `*.opus`)
2. Analyze codec/format compatibility
3. Convert/process as needed
4. Move originals to `processed/` folder
5. Print summary statistics

### Cross-platform Compatibility

Scripts use portable stat commands:
```bash
stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null
```
(macOS `-f%z` falls back to Linux `-c%s`)

## Dependencies

Required tools:
- `ffmpeg` - Media encoding/transcoding
- `ffprobe` - Media analysis
- `bc` - Floating-point calculations for frame comparison

## Common Workflows

### Processing New Downloaded Videos

1. Place MKV files in working directory
2. Run `./process_mkv.sh` to classify and add "(Video)" suffix
3. Run `./convert_mkv_to_mp4.sh` for lossless H.264+AAC files
4. Run `./reencode_all_mkv.sh` for remaining incompatible codecs

### Processing Audio Files

For Opus audio files: `./convert_opus_to_aac.sh`

### Output Formats

- Videos: MP4 (H.264 video + AAC audio, max 1080p)
- Audio: M4A (AAC 192kbps)
- All files optimized for Apple Music/iTunes import
