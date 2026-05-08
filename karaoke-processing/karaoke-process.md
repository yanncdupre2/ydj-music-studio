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

- `--sung-color HEX` *(v2)*
  Color of the sung lyrics (the band that the original tool renders as green). 6-digit hex, optional leading `#`. Default: `00C800`. Examples: `--sung-color FFA500` (orange), `--sung-color "#FF1493"` (deep pink).
  When non-default, output filename gets a `-sungXXXXXX` token appended to the threshold label (e.g., `bwg-40-80-sungFFA500`); default green keeps the legacy filename format.

- `-o DIR` *(v2)*
  Write outputs (preview PNGs and processed video) to `DIR` instead of the input file's directory. `DIR` is created if needed. Used by the GUI app to keep preview PNGs in a per-launch tmpdir; CLI users typically omit this.

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

- **Layout:** white unsung + orange (or other lower-luminance color) sung on black — sung is *darker* than unsung, the inverse of the Musisi pattern
- **Old guidance:** "Do not run through this tool. The LUT will invert sung↔unsung."
- **Current guidance (v2 only):** Run `karaoke-process-v2` with `--invert-bands` to swap the LUT polarity. Suggested starting params: `-lo 40 -hi 200 --invert-bands`.
- **Why it works:** with `--invert-bands` the LUT becomes black / green / white (low / mid / high). Orange sung text (luminance ~158) lands in the mid band → renders green. White unsung text (luminance 255) lands in the high band → renders white. Both bands map correctly.

### ROSÉ & Bruno Mars - APT. (Party Tyme channel)

- **Layout:** orange sung + bright white unsung on black, channel logo lower-left, ~5s splash intro card with title/artist
- **Recommended (v2):** `karaoke-process-v2 "input.mp4" -lo 40 -hi 200 -z 10 --invert-bands --corners-only -t 0% -r 0% -b 30% -l 15% -splash 4.5`
- **What that does:** keeps the first 4.5s splash unaltered; on the rest, masks only the bottom-left corner (large enough to cover the logo), zooms 10% for readability, applies the inverted LUT, and adds the default 4px outline halo (`--outline 2` is implicit).

## v2 Prototype: `karaoke-process-v2`

A parallel script `karaoke-processing/karaoke-process-v2` adds new options on top of the v1 pipeline. Once integrated and tested across all channels, it will replace the v1 script.

> v2 also has a SwiftUI front-end — see [`karaoke-process-gui`](#guikaraokeprocessgui) below — that drives the same script with live previews, presets, and a progress-bar-driven full encode. CLI usage is unchanged; the GUI is purely additive.

### `-splash SECONDS`

Preserve the first N seconds of the source unaltered (no mask, no LUT), then concatenate the processed remainder.

- Single-pass `concat` filter: no temp files, splash and body render at matching dims, then concatenate
- Audio is stream-copied from the input — bit-perfect, never decoded/re-encoded
- Accepts decimal values (e.g., `-splash 4.5`)
- Validation: must be > 0 and < video duration
- Ignored in still-frame mode (`-f`); a notice is printed
- Filename token: ` splash-N`

### `-z PERCENT`

Apply a uniform centered zoom of N% to the processed frames. Useful for thinner-font channels where lyric readability suffers at native scale.

- Implemented as `scale=iw*z:ih*z, crop=W:H` — output dims are unchanged (drop-in for FCP overlay layer)
- Splash frames are NOT zoomed — only body content
- Filter ordering inside the body: `mask → scale → crop → grayscale → LUT`. The LUT runs *after* the scale so the output stays deterministic 3-color (no gray/dark-green pixels at anti-aliased text edges)
- Validation: must be > 0 and ≤ 100
- Filename token: ` zoom-N`

### `--invert-bands`

Swap the mid and high output bands in the LUT:
- Default: low → black, mid → white, high → green
- With `--invert-bands`: low → black, mid → green, high → white

Use when sung text is at *lower* luminance than unsung text (Party Tyme and similar channels). Rescues channels previously documented as incompatible with this tool.

Filename token changes from `bwg-LO-HI` to `bgw-LO-HI` to indicate inverted band order.

### `--outline N` (default 2; 0 disables)

Add a high-contrast two-ring gray halo around the LUT'd text for readability when blended onto music videos. Built using stacked offset gray copies: stamp the LUT'd text shape at multiple offsets in gray, then place the colored text on top via alpha compositing so the colored core is preserved cleanly (no blend-mode desaturation).

For `--outline N`:
- **Outer stamps** at offsets ±2N (8 compass directions: N, NE, E, SE, S, SW, W, NW), gray 220, painted *first*
- **Inner stamps** at offsets ±N in the same 8 directions, gray 80, painted on top — overwrites the inner part of the outer ring
- **Original colored text** overlaid last at (0, 0), with black keyed transparent

Result: an N-wide bright outer ring (lifts text against dark backgrounds) plus an N-wide dark inner ring (gasket against bright backgrounds), total halo 2N wide. The "neon double-border" effect ensures legibility across any music video color underneath.

Defaults: `--outline 2` (4px halo total). Set `--outline 0` to disable. Maximum: 20.

Filter chain ordering inside the body: `mask → scale → crop → grayscale → LUT → outline`. Operating on the deterministic 3-color LUT output (rather than the raw frame) keeps the halo gray uniform and predictable.

For splash interaction, the outline pass lives only inside the body branch of the `filter_complex`; splash frames stay unaltered.

Filename token: ` outline-N` (omitted when N=0).

#### Why this approach (vs. native ffmpeg outline filters)

Earlier attempts using `gblur+blend` and edge filters produced poor / inconsistent results.

- **Deterministic:** every output pixel is one of `{0,0,0}`, `{80,80,80}`, `{220,220,220}`, or one of the LUT's three text colors — predictable for FCP blending
- **Configurable:** ring colors (currently fixed at 80 / 220) can be exposed as flags later; thickness via single `N` parameter
- **Reuses primitives we trust:** only `overlay` and `colorkey` — no per-pixel expression evaluation

#### Performance

The outline pass adds 16 overlay operations per frame (8 outer + 8 inner stamps) plus a final composite. Re-encode is ~3-4x slower than the no-outline case (e.g., the APT test went from ~40s to ~3 minutes for a 3-minute song).

When N=0, the outline filter chain is skipped entirely and the script falls back to the simpler `-vf` path — no performance hit.

#### Known limitation

At large N, the 8-stamp pattern produces a slight stair-step at the diagonal corners (gap of ~`N*(√2−1)` px in the radial direction). At `N≤4` it's invisible; at higher N values, a 16-stamp pattern would be needed to smooth it.

### `--bg-color HEX` (+ `--bg-strength`, `--bg-range`, `--bg-blend`)

Optional background-darken pass. Karafun-style channels render lyrics over a colored, *non-black* background (deep blue, olive, orange, etc.). The default LUT can't separate that bright background into the low-luminance bucket, so any non-black background bleeds into the white/green bands.

`--bg-color` activates a pre-LUT pass that pushes pixels matching a target color toward black, so the LUT can then quantize the result cleanly:

- `--bg-color HEX` — target background color (6-digit hex, optional leading `#`). **This flag activates the feature**; absence keeps the feature OFF.
- `--bg-strength N` (0–100, default 85) — how much to dim matched pixels. 100 = matched pixels become pure black; 0 = no dimming. Internally maps to a luma multiplier `K = (100 - N) / 100`.
- `--bg-range N` (0–100, default 35) — how wide a band of similar colors counts as background. Maps non-linearly to ffmpeg `colorkey` similarity (0.01 at N=0, 0.30 at N=100); the useful Karafun range is roughly N=20–60.
- `--bg-blend N` (0–100, default 10) — feathering at the match/no-match transition.

Filter chain ordering inside the body: `mask → bg-darken → scale → crop → grayscale → LUT → outline`. The bg-darken pass runs *after* the mask (so the user's mask choice still hides logos) and *before* the LUT (so the LUT sees a near-black background). Splash branch is unaffected — bg-darken only runs on body content.

Internally implemented as `colorkey` (RGB-distance) into an alpha mask, composited over a luma-scaled copy of the same frame. We initially tried `hsvkey` (hue-based) but discovered it's broken in ffmpeg 8.1 (output alpha stays at 255 even on exact-target inputs); `colorkey` is the working alternative.

Filename token: ` bg-RRGGBB-DSnn-CRnn-BLnn` (only when active).

Example — Depeche Mode (deep blue background):

```bash
karaoke-process-v2 "Depeche Mode - Shake The Disease.mp4" \
  --bg-color 4742B8 --bg-strength 95 --bg-range 35 --bg-blend 10 \
  -splash 5
```

For multi-hue backgrounds (varying brightness, color shifts) the technique can fall short — a fallback to multi-pass processing in Final Cut Pro is the documented escape hatch.

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
Video (v1):
Song Title [outer box-5-15-15-5 bwg-40-80].mp4

Still frame:
Song Title [frame-20 masked-outer box-20-20-20-20].png
Song Title [frame-20 processed-outer box-20-20-20-20 bwg-40-64].png

Corner-only still frame:
Song Title [frame-20 masked-corners box-5-20-20-5].png
Song Title [frame-20 processed-corners box-5-20-20-5 bwg-40-64].png

v2 with inverted LUT, zoom, outline, and splash:
Song Title [corners box-0-30-15-0 bgw-40-200 zoom-10 outline-2 splash-4_5].mp4

v2 with custom sung color (orange):
Song Title [outer box-5-15-15-5 bwg-40-80-sungFFA500 outline-2].mp4

v2 with background darken (DM blue-violet bg):
Song Title [outer box-5-15-15-5 bwg-40-80 bg-4742B8-DS95-CR35-BL10 outline-2 splash-5].mp4
```

## GUI: `karaoke-process-gui`

A SwiftUI macOS app that wraps `karaoke-process-v2` with a live-preview UI, persisted presets, and a foreground-progress full encode. Lives in `karaoke-processing/karaoke-process-gui/`. Built with Swift Package Manager → bundled as `KaraokeProcessGUI.app` via `build.sh`.

### Features

- **Three image panels** with white aspect-ratio borders that trace the actual video edges:
  - AVPlayer-based video player (top-left)
  - Mask + Zoom preview (bottom-left)
  - LUT + Outline preview (bottom-right) — the most important panel for verifying final output
- **Two-column parameters** (top-right) — Mask + Zoom on the left, Thresholds + Outline + Splash + Preset on the right
- **Sung text color picker** — standard macOS `NSColorPanel` (defaults to Crayons mode); the swatch sits next to the Invert bands toggle
- **Splash auto-capture** — toggling "Preserve intro splash" ON snaps the duration to the current playhead; user can edit the seconds field afterward
- **Persisted presets** at `~/Library/Application Support/KaraokeProcessGUI/presets.json` (pretty-printed, sorted-keys); seeded with `Sing King` and `Musisi` on first launch. "Save current as preset…" picks up a new name (with overwrite confirmation if it exists). Splash is intentionally NOT included in saved presets — it's always per-file.
- **Foreground processing with progress bar** — parses ffmpeg's `time=HH:MM:SS.ss` stderr lines vs. the asset's loaded duration. Cancel button kills the child cleanly; window-close also cancels. Done state shows "Reveal in Finder".
- **Quick Action wrapper** — `karaoke-processing/Karaoke Process v2.workflow/` is a single-Run-Shell-Script Automator service that does `open -a /Applications/KaraokeProcessGUI.app "$f"`. Drop it in `~/Library/Services/`.

### Build

```bash
cd karaoke-processing/karaoke-process-gui
./build.sh                                  # produces KaraokeProcessGUI.app, ad-hoc signed
mv KaraokeProcessGUI.app /Applications/
cp -R "../Karaoke Process v2.workflow" ~/Library/Services/
```

Then right-click any video in Finder → Quick Actions → **Karaoke Process v2**.

### Layout

```
+--------------------------+--------------------------------------------+
| Video player             | Margins / Zoom    | Thresholds + Sung color|
| (AVPlayer + AR border)   | (left col)        | Outline / Splash       |
|                          |                   | Preset                 |
|                          +-------------------+------------------------+
|                          | [↻ Refresh Previews]    ⌘R    t = M:SS.ss |
+--------------------------+--------------------------------------------+
| Mask + Zoom preview      | LUT + Outline preview                      |
| (AR border, dark bg)     | (AR border — full-aspect of final output)  |
+--------------------------+--------------------------------------------+
| status: idle / progress bar (% + ETA) / done / failed                  |
+------------------------------------------------------------------------+
```

### Why these UI choices

- **`NSViewRepresentable` around `AVPlayerView`** instead of SwiftUI's `VideoPlayer` — the latter depends on `_AVKit_SwiftUI`, which crashed at startup on macOS 26.3.1 with `getSuperclassMetadata` (saved as a feedback memory; see crash-reports archive)
- **Dynamic `videoAspectRatio`** computed from `AVAssetTrack.naturalSize × preferredTransform` — ensures the white border traces the *true* video edges, not letterboxed panel chrome
- **Manual progress refresh** (no live preview on slider drag) — each `-f` invocation takes 1–3s, too slow per tick
- **No nohup/detach for processing** — running ffmpeg as a foreground child means we can stream stderr for progress AND closing the window cancels cleanly; matches user expectation

```
~/Projects/ydj-music-studio/karaoke-processing/karaoke-process-v2 "/path/to/input.mp4" -t 5% -b 15% -l 15% -r 5% --corners-only -lo 40 -hi 80 --invert-bands -z 10 --outline 2 -splash 5
```
