#!/usr/bin/env python3
"""Remove bars baked into a music video: fill 16:9, or crop to the real picture.

Modes:
  fill  (default) non-linear horizontal stretch to 1920x1080: near-true shape
        in the centre, stretch ramping up toward the edges (cubic profile),
        after a small zoom that trims the top and bottom (--zoom).
  crop  just the picture, at its true shape (e.g. 1440x1080 for a 4:3 video),
        leaving players free to fill, stretch or crop it themselves.

The picture area is measured at full resolution (black bars first, then soft
side panels); --crop W:H:X:Y overrides it with a box from the scan report.
A 5:4 picture is taken to be 4:3 squeezed by a lost PAL pixel shape and is
widened back (override with --aspect).

Audio is stream-copied untouched, and MP4 tags (incl. the Serato / Mixed In
Key freeform atoms that ffmpeg drops) are copied from the source afterwards.

Usage:
    venv/bin/python pillarbox/widen.py VIDEO                   # "VIDEO [fill].mp4" next to it
    venv/bin/python pillarbox/widen.py VIDEO --mode crop       # "VIDEO [crop].mp4"
    venv/bin/python pillarbox/widen.py VIDEO --still 75        # preview the frame at 75 s as PNG
    venv/bin/python pillarbox/widen.py VIDEO --crop 1410:1080:256:0 -o ~/Desktop
"""

import argparse
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scan import MIN_BAR, PAL_SQUEEZED, find_bars, find_soft_sides, probe, sample_frames  # noqa: E402

OUT_W, OUT_H = 1920, 1080
SS = 4          # horizontal supersampling ahead of remap's nearest-neighbour lookup
INSET = 2       # px trimmed inside each detected edge (drops the soft transition column)


def even(v):
    return 2 * round(v / 2)


def detect_box(path, info):
    """Return the picture's (w, h, x, y) in source pixels, untrimmed and trimmed.

    The untrimmed box gives the shape; the trimmed one, pulled inside the
    fuzzy edges, is what gets cropped."""
    w, h = info["width"], info["height"]
    lit, bars = find_bars(sample_frames(path, info["duration"], size=(w, h)))
    if bars is None:
        sys.exit("Too few non-black frames to measure the picture; pass --crop")
    # Thin dark edges (capture junk) are trimmed too: unlike the scan's
    # classification, cropping wants every column that is black in all samples.
    left, right, top, bottom = bars
    soft = None
    if left < MIN_BAR * w or right < MIN_BAR * w:
        soft = find_soft_sides(lit, top, bottom)
        if soft:
            left, right = soft
            print(f"Soft side panels detected: {left} px / {right} px")
    raw = (w - left - right, h - top - bottom, left, top)
    margin = INSET + (int(0.005 * w) if soft else 0)  # soft panel edges are fuzzier
    left, right, top, bottom = (v + margin if v else 0 for v in (left, right, top, bottom))
    return raw, (even(w - left - right), even(h - top - bottom), even(left), even(top))


def parse_aspect(text):
    if ":" in text:
        n, d = text.split(":")
        return float(n) / float(d)
    return float(text)


def build_maps(workdir, a, ssw):
    """Output column u in [-1, 1] samples source column s = a*u + (1-a)*u^3."""
    u = (np.arange(OUT_W) + 0.5) / (OUT_W / 2) - 1
    s = a * u + (1 - a) * u ** 3
    xs = np.clip(np.round((s + 1) / 2 * ssw - 0.5), 0, ssw - 1).astype(">u2")
    maps = []
    for name, plane in (("xmap", np.tile(xs, (OUT_H, 1))),
                        ("ymap", np.repeat(np.arange(OUT_H, dtype=">u2")[:, None], OUT_W, axis=1))):
        path = Path(workdir) / f"{name}.pgm"
        with open(path, "wb") as f:
            f.write(f"P5\n{OUT_W} {OUT_H}\n65535\n".encode())
            plane.tofile(f)
        maps.append(path)
    return maps


def fill_graph(box, true_aspect, zoom, center, workdir):
    bw, bh, bx, by = box
    crop_h = even(bh / (1 + zoom))
    true_w_out = true_aspect * bh * OUT_H / crop_h  # undistorted picture width at output scale
    r = OUT_W / true_w_out                           # average stretch needed to fill the frame
    if r <= 1.01:
        sys.exit(f"Picture is already {true_aspect:.2f}:1 after zoom; use --mode crop")
    center = min(center, r)
    a = r / center
    if a >= 1.5:
        sys.exit(f"Picture is {true_aspect:.2f}:1, too narrow to fill without extreme edge stretch")
    profile = ", ".join(f"{u:.2f}: x{r / (a + 3 * (1 - a) * u * u):.2f}" for u in (0, 0.5, 0.75, 1))
    print(f"Stretch vs true shape by distance from centre (0 = centre, 1 = edge): {profile}")
    ssw = SS * round(true_w_out)
    xmap, ymap = build_maps(workdir, a, ssw)
    graph = (f"[0:v]crop={bw}:{crop_h}:{bx}:{by + (bh - crop_h) // 2},"
             f"scale={ssw}:{OUT_H}:flags=lanczos,format=yuv444p[s];"
             f"[s][1:v][2:v]remap,format=yuv420p,setsar=1[v]")
    return graph, ["-i", str(xmap), "-i", str(ymap)]


def copy_tags(src, dst):
    from mutagen import MutagenError
    from mutagen.mp4 import MP4
    try:
        s, d = MP4(src), MP4(dst)
    except MutagenError:
        print("Source is not an MP4; tags not copied")
        return
    if s.tags is None:
        if d.tags is not None:  # drop ffmpeg's encoder tag so the output is as tagless as the source
            d.delete()
        return
    if d.tags is None:
        d.add_tags()
    d.tags.clear()
    d.tags.update(s.tags)
    d.save()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--mode", choices=["fill", "crop"], default="fill")
    ap.add_argument("--zoom", type=float, default=0.05, help="fill: pre-zoom (0.05 trims 2.5%% top and bottom)")
    ap.add_argument("--center", type=float, default=1.08, help="fill: stretch at the centre vs true shape")
    ap.add_argument("--aspect", help="true shape of the picture, e.g. 4:3 (default: measured, 5:4 -> 4:3)")
    ap.add_argument("--crop", help="picture box W:H:X:Y in source pixels (skips detection)")
    ap.add_argument("-o", "--output-dir", help="default: next to the input")
    ap.add_argument("--still", type=float, help="write one PNG frame at this time instead of a video")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--force", action="store_true", help="overwrite an existing output")
    args = ap.parse_args()

    src = Path(args.input).resolve()
    info = probe(str(src))
    if args.crop:
        raw = box = tuple(int(v) for v in args.crop.split(":"))
    else:
        raw, box = detect_box(str(src), info)
    bw, bh, bx, by = box
    measured = float(Fraction(raw[0], raw[1]) * info["sar"])
    corrected = True
    if args.aspect:
        true_aspect = parse_aspect(args.aspect)
    elif PAL_SQUEEZED[0] <= measured < PAL_SQUEEZED[1]:
        true_aspect = 4 / 3
        print(f"Picture measures {measured:.3f}:1, treated as 4:3 squeezed by lost PAL pixel shape")
    else:
        true_aspect, corrected = measured, False
    print(f"Picture box {bw}x{bh} at {bx},{by} in a {info['width']}x{info['height']} frame; "
          f"true shape {true_aspect:.3f}:1")

    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{src.stem} [{args.mode}]"
    out = out_dir / (f"{stem} {args.still:g}s.png" if args.still is not None else f"{stem}.mp4")
    if out.exists() and not args.force and args.still is None:
        sys.exit(f"Output exists: {out} (use --force to overwrite)")

    with tempfile.TemporaryDirectory() as workdir:
        if args.mode == "fill":
            graph, extra_inputs = fill_graph(box, true_aspect, args.zoom, args.center, workdir)
        else:
            # Without a shape correction, only non-square pixels are resampled (to square);
            # square-pixel sources are cropped with no scaling at all.
            out_w = even(bh * true_aspect) if corrected else even(bw * info["sar"])
            graph, extra_inputs = (f"[0:v]crop={bw}:{bh}:{bx}:{by},"
                                   f"scale={out_w}:{bh}:flags=lanczos,setsar=1[v]"), []

        cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-stats", "-y"]
        if args.still is not None:
            cmd += ["-ss", str(args.still), "-i", str(src), *extra_inputs,
                    "-filter_complex", graph, "-map", "[v]", "-frames:v", "1", str(out)]
            subprocess.run(cmd, check=True)
            print(f"Created: {out}")
            return

        color = []
        for key, flag in (("color_space", "-colorspace"), ("color_primaries", "-color_primaries"),
                          ("color_transfer", "-color_trc")):
            if key in info["color"]:
                color += [flag, info["color"][key]]
        cmd += ["-i", str(src), *extra_inputs, "-filter_complex", graph,
                "-map", "[v]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf), "-pix_fmt", "yuv420p", *color,
                "-c:a", "copy", "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True)
    copy_tags(str(src), str(out))
    print(f"Created: {out}")


if __name__ == "__main__":
    main()
