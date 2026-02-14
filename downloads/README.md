# Downloads - YouTube Media Processing

Efficient batch conversion of YouTube-downloaded content (MKV/Opus) to Apple ecosystem-compatible formats (MP4/M4A).

## Problem Statement

YouTube download utilities (yt-dlp, etc.) recently changed default output formats:
- Videos: MKV instead of MP4
- Audio: Opus instead of AAC

**Issues:**
- macOS QuickLook doesn't preview MKV files well
- Apple Music doesn't support Opus audio
- Need efficient batch conversion for new downloads

## Processing Pipeline

### 1. MKV Classification (`process_mkv.sh`)
Distinguishes between real videos and static image videos:
- Samples frames at 10%, 50%, and 90% of video duration
- Compares frame similarity (threshold: 5% difference)
- **Static images:** Extracts audio stream, deletes MKV
- **Real videos:** Renames with "(Video)" suffix for later processing

### 2. Lossless Remuxing (`convert_mkv_to_mp4.sh`)
Fast container conversion without re-encoding:
- Only processes MKV files with H.264/H.265 video + AAC audio
- Uses `ffmpeg -c copy` for bit-perfect stream copy
- Incompatible codecs (VP9, Opus) are skipped
- Moves original to `processed/` folder

### 3. Transcoding (`reencode_mkv_to_mp4.sh`, `reencode_all_mkv.sh`)
Re-encodes incompatible codecs:
- **Video:** VP9 → H.264 (CRF 21-22 based on file size)
- **Audio:** Opus → AAC 192kbps
- **Resolution:** Automatic 4K → 1080p downscaling
- Dynamic quality: Files <50MB use CRF 21, ≥50MB use CRF 22

### 4. Audio Conversion (`convert_opus_to_aac.sh`)
Converts standalone Opus audio files:
- Opus → M4A (AAC 192kbps)
- Apple Music-compatible format

## Usage

### Process New Downloads

1. Download YouTube content to working directory
2. Run processing scripts in order:

```bash
cd ~/Projects/ydj-music-studio/downloads

# Step 1: Classify MKVs (extract audio from static videos)
./process_mkv.sh

# Step 2: Fast remux for compatible files
./convert_mkv_to_mp4.sh

# Step 3: Transcode remaining incompatible files
./reencode_all_mkv.sh

# Step 4: Convert Opus audio files
./convert_opus_to_aac.sh
```

### Individual File Processing

```bash
# Process single MKV file
./reencode_mkv_to_mp4.sh "filename.mkv"
```

## Output Formats

- **Videos:** MP4 (H.264 video + AAC audio, max 1080p)
- **Audio:** M4A (AAC 192kbps)
- All files optimized for Apple Music/iTunes import with `+faststart` flag

## File Organization

```
downloads/
├── *.mkv, *.opus          # Working files (before processing)
├── *.mp4, *.m4a           # Processed files (after conversion)
└── processed/             # Original files moved here after successful conversion
```

**Note:** Working and processed media files are gitignored.

## Dependencies

### Required: ffmpeg/ffprobe
```bash
brew install ffmpeg
```

### Tools Used
- `ffprobe` - Media analysis (codec detection, resolution, frame comparison)
- `ffmpeg` - Media conversion and transcoding
- `bc` - Floating-point calculations for frame similarity

## Configuration

### Video Quality (`reencode_mkv_to_mp4.sh`)
- **CRF 21** - Files <50MB (higher quality)
- **CRF 22** - Files ≥50MB (smaller size)
- **Preset:** medium (balanced speed/quality)
- **Max resolution:** 1080p (4K auto-downscaled)

### Audio Quality
- **AAC bitrate:** 192kbps
- **Sample rate:** Auto-detected from source

### Frame Similarity Threshold (`process_mkv.sh`)
- **Threshold:** 5% difference between sampled frames
- Lower = stricter (more likely to classify as real video)
- Higher = looser (more likely to classify as static image)

## Safety Features

- Original files moved to `processed/` (not deleted)
- Dry-run capability (can be added to scripts)
- Summary statistics after each run
- Cross-platform stat commands (macOS + Linux compatible)

## Common Workflows

### Batch Process Downloaded Music Videos
```bash
# Downloads are in ~/Downloads/YDJ/
cd ~/Downloads/YDJ/
~/Projects/ydj-music-studio/downloads/process_mkv.sh
~/Projects/ydj-music-studio/downloads/convert_mkv_to_mp4.sh
~/Projects/ydj-music-studio/downloads/reencode_all_mkv.sh

# Import MP4s to Apple Music
# Move to ~/Downloads/YDJ/processed/ when done
```

### Extract Audio from Video Files
```bash
./process_mkv.sh  # Handles static image videos
# For real videos, manually extract with:
ffmpeg -i "video.mkv" -vn -c:a copy "audio.m4a"
```

## Performance

### Lossless Remux (convert_mkv_to_mp4.sh)
- **Speed:** Very fast (seconds per file)
- **Quality:** Bit-perfect copy, no quality loss

### Transcoding (reencode_mkv_to_mp4.sh)
- **Speed:** Depends on file size and resolution
  - 1080p video: ~1-2x real-time (3min video → 3-6min encoding)
  - 4K video: ~0.5x real-time (3min video → 6-12min encoding)
- **Quality:** High (CRF 21-22), visually lossless for most content

## Future Enhancements

- Dry-run mode (preview without converting)
- Parallel processing for batch operations
- Quality presets (high/medium/low)
- Integration with yt-dlp for direct download+convert pipeline
- Auto-import to Apple Music after conversion
