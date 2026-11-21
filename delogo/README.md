# Delogo: remove fixed overlays burned into a music video

Some YouTube re-edits carry a channel logo or a block of credit text
("Artist / Title / Video Edition / Promotional Use Only") burned into the
picture. `delogo.py` finds those overlays on its own, whatever their colour,
and erases them for the time they are on screen.

```bash
venv/bin/python delogo/delogo.py VIDEO                 # "VIDEO [delogo].mp4" next to it
venv/bin/python delogo/delogo.py VIDEO --detect-only   # report + preview image only (seconds)
venv/bin/python delogo/delogo.py VIDEO --skip 2        # leave overlay 2 alone (a false hit)
venv/bin/python delogo/delogo.py VIDEO --include 3     # also remove static-scene overlay 3
venv/bin/python delogo/delogo.py VIDEO -o ~/Desktop
```

The original is never touched. Each run prints the overlays it found, numbered,
with position and on-screen times, and writes a preview to
`delogo/data/previews/<name> [delogo].png` (gitignored): one row per overlay,
masked area tinted red on the left, the result on the right. Check it before
trusting the video; numbers are stable between runs, so `--skip` takes them as
printed.

## Putting a result into the library

Watch the `[delogo].mp4`, then swap it in place with pillarbox's `apply.py`.
The path Apple Music knows stays the same, and the original is kept as
`<name>-backup.mp4` until you discard it:

```bash
venv/bin/python delogo/delogo.py VIDEO                    # 1. render "VIDEO [delogo].mp4" next to it, watch it
venv/bin/python pillarbox/apply.py --delogo VIDEO         # 2. backup, verify, swap in, log
venv/bin/python pillarbox/apply.py --restore VIDEO        #    undo, if needed
venv/bin/python pillarbox/apply.py --trash-backups VIDEO  # 3. once happy: backup to the Trash
```

`apply.py --delogo` never renders anything itself, so nothing goes into the
library unwatched. It skips a video whose `[delogo].mp4` is missing (render
without `-o`, so it lands next to the video), older than the video, or a
different picture size. Details in `pillarbox/README.md`.

A video that also needs pillarbox treatment: delogo first, then pillarbox.
The fill stretches the picture up to ~2x toward the edges, which would widen
a corner logo's strokes and smudge its fill. Each fix is its own encode and
needs the previous backup discarded first.

## How it works

1. **Find** (2 fps): over sliding 8 s windows, keep pixels that are an edge in
   at least 85% of the frames while the area around them changes. Edges come
   from colour steps in any channel, so white, coloured and semi-transparent
   overlays are all found. Black bars (detected per window, since bars can come
   and go between sections) and a thin frame margin are excluded, because a
   bar's edge also holds still while the picture beside it changes.
2. **Track** (4 fps): for each candidate, score every frame by how many of its
   edges are present, compared with the background around it. Hysteresis,
   2 s gap bridging and 0.5 s of padding each side (fades) give the on-screen
   spans.
3. **Mask**: the edges that persist while on screen, the colour-stable pixels
   next to them (the inside of thick strokes), and any small enclosed gap (a
   logo's disc, the inside of an O). Left unmasked, those gaps would be smeared
   outward by the fill.
4. **Fill**: ffmpeg's `removelogo` rebuilds each masked pixel from the nearest
   unmasked ones, one filter per overlay, enabled only during its spans.

Audio is stream-copied and MP4 tags (Serato / Mixed In Key atoms included) are
copied across with `pillarbox/widen.py`'s `copy_tags`. The output is then
checked with `pillarbox/apply.py`'s `verify()`: same shown frames, identical
audio packets and data, identical tags. Video is libx264 `-preset slow -crf 18`.

Speed: detection takes about 25 s for a 5-minute 720p video; the full run
including the encode takes about 1.5 minutes.

## Limits

- **Fill quality** depends on the footage. Thin strokes over soft (upscaled SD)
  footage disappear almost completely. Over sharp detail or bright edges you
  can see a faint smudge in the letters' shape. The upgrade path for that
  is flow-guided video inpainting (e.g. ProPainter), which copies real pixels
  from neighbouring frames of the same shot. It is not built.
- **Static scenes with changing light** can be mistaken for overlays: a fixed
  camera on a flickering room keeps its edges in place while the brightness
  changes (seen on Metallica "One", 7:31). Candidates seen only over a
  scene that never changes are reported but not removed (`--include N`); this
  flicker case gets past that check, so look at the preview and use `--skip N`.
- **Overlays that move** (scrolling tickers, animated logos) are not handled,
  and neither is an overlay sitting on a black bar, since nothing behind it
  ever changes.
- A **semi-transparent banner** behind text is only removed along its edges;
  its darkened area stays.
- Built for **chosen videos**, not a library sweep. Most videos have no overlay,
  detection takes ~25 s each, and every false hit would cost a re-encode.
