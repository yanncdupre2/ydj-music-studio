# `karaoke-process`

Command-line utility for masking karaoke videos and remapping luminance to fixed colors.

## Goal

Prepare YouTube karaoke videos for overlay blending onto music videos in Final Cut Pro. The output is designed to be combined with a music video using `screen` or `add` blend modes, where:

- Pure black background → renders as transparent in the blend
- White unsung text and green sung text → bright, high-contrast against any underlying footage
- Channel logos and watermarks → masked out so they don't bleed into the overlay

The luminance-LUT approach (vs. a per-pixel color match like `geq`) is near realtime on 1080p and makes the output fully deterministic: every visible pixel ends up as one of three exact RGB values — black `(0,0,0)`, white `(255,255,255)`, or green `(0,200,0)`. There is no glow effect; if you want a bloom around the lyrics, apply it as a separate effect inside FCP after blending.

## What It Does

The script:

1. Masks part of the frame with black
2. Converts the remaining image to grayscale
3. Remaps luminance to fixed output colors:
   - black = `0,0,0`
   - white = `255,255,255`
   - green = `0,200,0`

It works on a video file located anywhere on disk and writes outputs next to the input file.

## Installation

The command is installed at:

```bash
~/.local/bin/karaoke-process
```

If `~/.local/bin` is on your `PATH`, you can run it from anywhere as:

```bash
karaoke-process ...
```

## Usage

```bash
karaoke-process INPUT_FILE [options]
```

## Defaults

If you do not specify overrides, the script uses masked margins of:

- `-t 5%`
- `-b 15%`
- `-l 15%`
- `-r 5%`
- `-lo 40`
- `-hi 80`

## Options

- `-t TOP%`
  Top margin to black out, as percent of height.

- `-b BOTTOM%`
  Bottom margin to black out, as percent of height.

- `-l LEFT%`
  Left margin to black out, as percent of width.

- `-r RIGHT%`
  Right margin to black out, as percent of width.

- `-lo LOW`
  Lower luminance threshold.

- `-hi HIGH`
  Upper luminance threshold.

- `-f SECONDS`
  Still-frame mode. Extracts only the frame at the given timestamp and generates PNGs instead of processing the full video.

- `--corners-only`
  Masks only the corners implied by the provided margins.

  Without this flag, the script blacks out all content in the specified margins using full strips:
  - top strip
  - bottom strip
  - left strip
  - right strip

  With this flag, it blacks out only:
  - top-left corner
  - top-right corner
  - bottom-left corner
  - bottom-right corner

- `-h` or `--help`
  Shows help.

## Full Video Mode

If `-f` is not present:

- the full video is processed
- audio is copied
- output video is encoded as `yuv420p`
- chapters and data tracks are removed to avoid bad timeline metadata in the output

Example:

```bash
karaoke-process "/path/to/video.mp4"
```

Example with custom thresholds:

```bash
karaoke-process "/path/to/video.mp4" -lo 24 -hi 80
```

Example with custom box:

```bash
karaoke-process "/path/to/video.mp4" -t 20% -b 20% -l 20% -r 20% -lo 24 -hi 80
```

## Still Frame Mode

If `-f N` is present, the script processes only the frame at `N` seconds and creates two PNGs:

1. masked-only PNG
2. fully processed PNG

Example:

```bash
karaoke-process "/path/to/video.mp4" -f 90
```

Example with custom thresholds:

```bash
karaoke-process "/path/to/video.mp4" -lo 40 -hi 64 -f 20
```

## Corner-Only Masking Example

If you want to remove only a lower-left logo area while keeping more of the side text visible, use:

```bash
karaoke-process "/path/to/video.mp4" -b 20% -l 20% --corners-only -f 20
```

That masks only the corners implied by the margins, instead of masking the full left and bottom strips.

## Channel-Specific Starting Points

Recommended starting parameters per known karaoke channel. **Always run with `-f SECONDS` on a representative timestamp first** to verify thresholds and mask geometry before processing the full video — the still-frame round-trip costs about a second and saves a 4-minute re-encode.

### Musisi Karaoke

- **Layout:** orange sung text, dimmer white unsung, black background, channel logo in the lower-left (~330×300 px on 1080p ≈ 17% width × 28% height)
- **Recommended:** defaults — `karaoke-process input.mp4`
- **Tighter mask** (preserves more visible side text, kills only the logo corner): `-l 17% -b 28% --corners-only`
- **Why the defaults work:** bright orange sung text has higher luminance than the dimmed unsung text, so it falls into the high band and renders green; the dimmer unsung text falls into the mid band and renders white

### Sing King

- **Layout:** thinner pink/orange font, different from Musisi
- **Status:** untested with the new tool — needs a tuning pass
- **Suggested first try:** `-lo 30 -hi 65 -f 30` (lower thresholds because the thinner font has fewer high-luminance pixels)
- **TODO:** confirm logo position and finalize mask margins

### Party Tyme

- **Layout:** typically white unsung + green sung on black — already close to the desired output format
- **Recommendation:** likely *do not* run through this tool. The luminance LUT will invert green↔white because pure white (luminance 255) lands in the high band → mapped to green, while pure green (luminance ~75) lands in the mid band → mapped to white
- **If you only need logo masking:** consider a plain `ffmpeg drawbox` pass instead, since the `-lo`/`-hi` LUT cannot be bypassed in this tool

## Tuning Workflow

The fast iteration loop for any new channel:

1. Pick a representative timestamp (a moment with both sung and unsung text on screen)
2. Run with `-f SECONDS` and the proposed parameters → compare the two output PNGs in Preview
3. Adjust `-lo` (raise to push more dim pixels to black; lower to recover faint text) and `-hi` (raise to keep more text white; lower to push more text to green)
4. Adjust margins until logos/watermarks are masked but lyrics are preserved; switch to `--corners-only` if full strips eat too much of the lyrics line
5. Once the still frame looks right, drop `-f` and let the full video render

## Output Naming

The script auto-generates output names next to the source file.

Examples:

```text
Video:
Song Title [outer box-5-15-15-5 bwg-40-80].mp4

Still frame:
Song Title [frame-20 masked-outer box-20-20-20-20].png
Song Title [frame-20 processed-outer box-20-20-20-20 bwg-40-64].png

Corner-only still frame:
Song Title [frame-20 masked-corners box-5-20-20-5].png
Song Title [frame-20 processed-corners box-5-20-20-5 bwg-40-64].png
```
