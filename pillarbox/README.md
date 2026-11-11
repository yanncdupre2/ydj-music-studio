# Pillarbox: find and fix music videos that don't fill 16:9

Many older music videos were uploaded as 1920x1080 files with black (or
blurred) side bars baked into the picture, so no player setting can fill the
screen. Two tools:

| Script | What it does |
|---|---|
| `scan.py` | Scans a playlist (default `MASTER LIST DJ VIDEO`) and reports every video whose picture doesn't fill the frame. Read-only. |
| `widen.py` | Fixes one video: non-linear fill to 1920x1080, or crop to the real picture. Writes a new file; never touches the original. |
| `apply.py` | Converts library videos **in place** with `widen.py`, keeping a `-backup` copy of each original next to it, and logs every conversion so it can be restored. |

Run both with the project venv (`venv/bin/python`): `scan.py` needs numpy,
`widen.py` needs mutagen for tag copying.

## scan.py

```bash
venv/bin/python pillarbox/scan.py                  # whole playlist (cached re-runs are instant)
venv/bin/python pillarbox/scan.py --rescan         # ignore the cache
venv/bin/python pillarbox/scan.py FILE [FILE ...]  # specific files
open pillarbox/data/report.html
```

How it works: the playlist's file paths come from the library database via
`common/playlist_paths.swift` (iTunesLibrary framework: ~9 s for 2,400
tracks, against ~7 min asking Music.app over AppleScript). Each video then
gets one ffprobe plus 8 keyframes decoded at 640x360 from 10%..90% of its
running time. A column counts as bar only when it is dark in every sample, so
dark scenes and fades don't trigger false hits. Results are cached in
`data/scan-cache.json` by path + size + mtime + `ANALYSIS_VERSION`.

Outputs (gitignored, under `pillarbox/data/`): `report.csv` (one row per
video, with the crop box `W:H:X:Y` in source pixels) and `report.html`
(a thumbnail per flagged video with the detected picture area outlined in red).

| Category | Meaning | Fix |
|---|---|---|
| `pillarbox-5x4` | Black side bars around a 5:4 picture: a 4:3 PAL video whose pixel shape was lost, so it is ~6% too narrow | `widen.py` (fill or crop; shape corrected automatically) |
| `pillarbox-4x3` | Black side bars around a true 4:3 picture | `widen.py` |
| `letterbox-in-4x3` | Widescreen picture letterboxed inside a 4:3 file: bars on all four sides on a 16:9 screen | `widen.py --mode crop` (no stretch needed) |
| `soft-sides` | Possible side panels with no real picture (blurred copy or flat fill). Low confidence | Check thumbnail, then `widen.py` |
| `pillarbox-other` | Side bars around some other shape | Check thumbnail |
| `native-narrow` | The file itself is narrower than 16:9 (e.g. 640x480); players add the bars | `widen.py` if 4:3 |
| `pillarbox-vertical` | Portrait (phone) picture | Leave: too narrow to stretch |
| `letterbox` | Bars top and bottom only (widescreen film) | Usually leave |
| `uncertain` / `error` / `missing` | Too dark to judge / unreadable / no local file | Inspect |

Soft panels are detected from a sharp step in fine detail at mirrored
positions on both sides. Averaged over 8 scenes, natural soft focus fades
gradually, while a pasted-in panel edge sits at the same column in every frame.

## widen.py

```bash
venv/bin/python pillarbox/widen.py VIDEO                  # "VIDEO [fill].mp4" next to the input
venv/bin/python pillarbox/widen.py VIDEO --mode crop      # "VIDEO [crop].mp4": bars removed, true shape
venv/bin/python pillarbox/widen.py VIDEO --still 75 -o ~/Desktop   # preview one frame as PNG
venv/bin/python pillarbox/widen.py VIDEO --crop 1410:1080:256:0    # box from report.csv
```

- **Fill** (default) stretches horizontally along a cubic curve, so the
  centre stays near true shape and the stretch builds toward the edges
  (the "non-linear stretch" TVs call Panorama / Wide Zoom). Defaults:
  `--zoom 0.05` (trims 2.5% top and bottom) and `--center 1.08`, which for a
  4:3 source gives x1.08 at the centre, x1.22 halfway out and x1.95 at the
  very edge. Implemented with ffmpeg's `remap` filter over a 4x horizontally
  supersampled source, because `remap` samples nearest-neighbour.
- **Crop** outputs just the picture at its true shape, for players that can
  fill, stretch or crop on their own. Square-pixel sources are cropped with
  no scaling at all; only a shape correction (5:4 -> 4:3, `--aspect`) or
  non-square source pixels cause resampling.
- The picture box is re-measured at full resolution, and edges are trimmed
  2 px inside (plus 0.5% for soft panels) so fuzzy edge columns don't get
  stretched into visible lines.
- A measured 5:4 picture is treated as squeezed 4:3 and widened back
  (`--aspect` overrides, e.g. `--aspect 5:4` to keep it).
- Audio is stream-copied bit-for-bit, so cue points stay aligned. MP4 tags,
  including the Serato (`com.serato.dj`) and Mixed In Key
  (`com.mixedinkey.mixedinkey`) freeform atoms that ffmpeg drops, are copied
  across with mutagen.
- Video: libx264 `-preset slow -crf 18`. Expect files 2-3x the size of a
  low-bitrate YouTube source. Raise `--crf` to shrink them.

## apply.py (in-place library conversion)

```bash
venv/bin/python pillarbox/apply.py VIDEO [VIDEO ...]            # convert, keeping "<name>-backup.mp4"
venv/bin/python pillarbox/apply.py --restore VIDEO [VIDEO ...]  # undo
venv/bin/python pillarbox/apply.py --trash-backups VIDEO [VIDEO ...]  # once checked: backups to the Trash
```

Per video: clone the original to `<name>-backup<ext>` in the same folder
(APFS clone, so it costs no extra space until the original is replaced),
run `widen.py`, verify the result, then rename the converted file over the
original. The path Apple Music knows never changes, so nothing needs
re-importing. If verification fails, the original is left untouched and the
backup goes to the Trash. A video that already has a `-backup` is skipped,
so a second run can't overwrite the real original.

Verification compares what is actually played, not container header counts
(old YouTube uploads often disagree with themselves):
- video: same number of shown frames (pre-roll frames with negative
  timestamps and empty MPEG-4 Part 2 "not coded" placeholders don't count,
  since ffmpeg drops both) and durations within 0.1 s;
- audio: identical packet list (timestamps, durations, sizes) and identical
  data checksum, so cue points stay aligned;
- tags: identical (a tagless source stays tagless).

The mode comes from the video's scan category (current cache entry):

| Category | Mode |
|---|---|
| `letterbox-in-4x3` | crop |
| `pillarbox-4x3` | crop (no zoom, no stretch) |
| `pillarbox-5x4` | fill with `--aspect 4:3` (shape corrected, 5% zoom, non-linear stretch) |

Other categories need an explicit `--mode`. Every outcome is appended to
`pillarbox/data/conversions.log` (tab-separated: time, status, category,
original, backup, detail). `--restore` moves the converted file to the
Trash and renames the backup back.
`--trash-backups` moves each video's backup to the Trash once you've checked
the results, and only if the converted file is in place. Trashing uses
macOS's `/usr/bin/trash`, which renames on name clashes (two artists'
`Apologize (Video)-backup.mp4`) and keeps Finder's Put Back.
