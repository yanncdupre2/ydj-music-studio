#!/usr/bin/env python3
"""Remove fixed overlays (channel logos, credit text) burned into a music video.

Detection does not depend on the overlay's colour: an overlay is a set of edges
that stay put while the picture underneath changes.
  Pass 1 samples the video at 2 fps and, over sliding 8 s windows, keeps pixels
  that are an edge in >= 85% of the frames while the area around them changes.
  Nearby hits are grouped into candidate overlays.
  Pass 2 samples at 4 fps to find when each candidate is on screen (its edges
  present, compared with the background around it), then builds its mask from
  the on-screen frames: edges that persist, plus colour-stable pixels next to
  them (the inside of thick strokes).
A candidate seen only over a static scene is reported but left alone, because
a static background edge behaves the same way (--include N to remove it).

Removal is ffmpeg's removelogo, which rebuilds each masked pixel from the
nearest unmasked ones, switched on only while that overlay is on screen. It
works best on thin strokes over soft footage; large solid shapes leave a smudge.

Audio is stream-copied and MP4 tags (incl. the Serato / Mixed In Key atoms) are
copied across, then the result is checked with pillarbox/apply.py's verify():
same shown frames, identical audio packets and data, identical tags.

Usage:
    venv/bin/python delogo/delogo.py VIDEO                 # "VIDEO [delogo].mp4" next to it
    venv/bin/python delogo/delogo.py VIDEO --detect-only   # report + preview image only
    venv/bin/python delogo/delogo.py VIDEO --skip 2        # leave overlay 2 alone
    venv/bin/python delogo/delogo.py VIDEO --include 3     # also remove static-scene overlay 3
    venv/bin/python delogo/delogo.py VIDEO -o ~/Desktop

Once the [delogo].mp4 is watched, `pillarbox/apply.py --delogo VIDEO` swaps it in
place of the library file, keeping a -backup (render without -o so it finds it).
"""

import argparse
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pillarbox"))

from apply import verify  # noqa: E402
from scan import probe  # noqa: E402
from widen import copy_tags  # noqa: E402

DATA_DIR = HERE / "data"

# Pass 1: candidates
DETECT_FPS = 2
WINDOW = 8             # s an overlay must hold still to be found
PERSIST = 0.85         # ...being an edge in >= 85% of the window's frames
EDGE = 30              # colour step across 2 px (any channel) that counts as an edge
CHANGE = 12            # luma std over a window above which a pixel has changed
NEAR = 8               # px radius around a held edge checked for change...
NEAR_CHANGED = 0.3     # ...of which >= 30% must have changed (rules out static shots)
BLOCK = 16             # hits within about one block of each other form one candidate
MIN_PIXELS = 40        # smaller candidates are noise
MIN_SIDE = 10          # px; thinner candidates are bar boundaries, not overlays
LINE = 0.5             # a row/column that is >= 50% edge is a bar boundary
DARK = 24              # luma at or below which a pixel is black
BAR = 0.9              # a row/column >= 90% black throughout a window is part of a bar...
BORDER = 6             # ...and edges within 6 px of a bar are ignored (soft VHS borders)
MARGIN = 0.015         # edges this close to the frame edge (fraction of height) are ignored

# Pass 2: when each candidate is on screen, and its final mask
TRACK_FPS = 4
ON, OFF = 0.35, 0.2    # presence score hysteresis: edge recall on the overlay minus around it
BRIDGE = 2.0           # s; shorter gaps (a bright shot hiding a white logo) are bridged
MIN_ON = 1.0           # s; shorter appearances are dropped
PAD = 0.5              # s added each side so fades are covered
STATIC_VIEW = 12       # mean luma std of the whole picture during an appearance below
                       # which the scene never changed, so the "overlay" may be background
KEEP_EDGE = 0.6        # the mask keeps pixels that are an edge in >= 60% of on-screen frames...
STABLE = 8             # ...plus pixels within FILL_R px of them whose luma std is below this
FILL_R = 6
HOLE = 0.002           # enclosed gaps up to this fraction of the frame are masked too (a logo's
                       # disc, letter counters): left alone, removelogo smears them outward
GROW = 1               # px margin for anti-aliasing and compression ringing
SAME_SPAN = 1.0        # s; candidates whose appearances match this closely are one overlay


def frames(path, fps, w, h):
    """Yield (time, rgb frame) sampled at fps."""
    size = w * h * 3
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", str(path), "-vf", f"fps={fps}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as p:
        i = 0
        while len(buf := p.stdout.read(size)) == size:
            yield i / fps, np.frombuffer(buf, np.uint8).reshape(h, w, 3)
            i += 1


def edges(rgb):
    """Pixels with a colour step >= EDGE across 2 px, horizontally or vertically, in any channel."""
    f = rgb.astype(np.int16)
    e = np.zeros(rgb.shape[:2], bool)
    e[:, 1:-1] = np.abs(f[:, 2:] - f[:, :-2]).max(axis=2) >= EDGE
    e[1:-1, :] |= np.abs(f[2:] - f[:-2]).max(axis=2) >= EDGE
    return e


def luma(rgb):
    f = rgb.astype(np.uint16)
    return ((77 * f[..., 0] + 150 * f[..., 1] + 29 * f[..., 2]) >> 8).astype(np.uint8)


def dilate(m, r):
    """Square dilation by r px."""
    v = m.copy()
    for d in range(1, r + 1):
        v[d:] |= m[:-d]
        v[:-d] |= m[d:]
    out = v.copy()
    for d in range(1, r + 1):
        out[:, d:] |= v[:, :-d]
        out[:, :-d] |= v[:, d:]
    return out


def fill_holes(m, max_size):
    """Add to m every enclosed gap (not reachable from the border) of up to max_size pixels."""
    free = ~m
    outside = np.zeros_like(m)
    outside[[0, -1]] = free[[0, -1]]
    outside[:, [0, -1]] = free[:, [0, -1]]
    while True:
        grown = outside.copy()
        grown[1:] |= outside[:-1]
        grown[:-1] |= outside[1:]
        grown[:, 1:] |= outside[:, :-1]
        grown[:, :-1] |= outside[:, 1:]
        grown &= free
        if (grown == outside).all():
            break
        outside = grown
    holes = free & ~outside
    out = m.copy()
    seen = np.zeros_like(m)
    h, w = m.shape
    for sy, sx in zip(*np.nonzero(holes)):
        if seen[sy, sx]:
            continue
        seen[sy, sx] = True
        pixels, stack = [], [(sy, sx)]
        while stack:
            y, x = stack.pop()
            pixels.append((y, x))
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and holes[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    stack.append((yy, xx))
        if len(pixels) <= max_size:
            out[tuple(np.array(pixels).T)] = True
    return out


def box_mean(m, r):
    """Mean of m over the (2r+1)^2 square around each pixel, clipped at the borders."""
    h, w = m.shape
    c = np.pad(m.astype(np.float32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    y0, y1 = np.clip(np.arange(h) - r, 0, h), np.clip(np.arange(h) + r + 1, 0, h)
    x0, x1 = np.clip(np.arange(w) - r, 0, w), np.clip(np.arange(w) + r + 1, 0, w)
    s = c[y1][:, x1] - c[y0][:, x1] - c[y1][:, x0] + c[y0][:, x0]
    return s / ((y1 - y0)[:, None] * (x1 - x0)[None, :])


# ---------------------------------------------------------------------------
# Pass 1: pixels that hold still as an edge while their surroundings change
# ---------------------------------------------------------------------------
def find_candidates(path, info):
    w, h = info["width"], info["height"]
    n = WINDOW * DETECT_FPS
    need = int(np.ceil(PERSIST * n))
    window = deque()
    count = np.zeros((h, w), np.uint8)
    s = np.zeros((h, w), np.int32)
    sq = np.zeros((h, w), np.int32)
    held_anywhere = np.zeros((h, w), bool)
    for i, (_, rgb) in enumerate(frames(path, DETECT_FPS, w, h)):
        e, y = edges(rgb), luma(rgb).astype(np.int32)
        window.append((e, y))
        count += e
        s += y
        sq += y * y
        if len(window) > n:
            e0, y0 = window.popleft()
            count -= e0
            s -= y0
            sq -= y0 * y0
        if len(window) == n and i % DETECT_FPS == 0:  # once a second
            held = count >= need
            if held.any():
                changed = sq / n - (s / n) ** 2 > CHANGE ** 2
                held &= box_mean(changed, NEAR) >= NEAR_CHANGED
                held_anywhere |= held & ~bar_zone(np.max([y for _, y in window], axis=0))
    return held_anywhere


def bar_zone(brightest):
    """Black bars in a window (full rows/columns at the frame edges) plus BORDER px, and a
    thin frame margin. A bar's edge never moves while the picture beside it changes, just
    like an overlay; bars can also come and go between sections of a video."""
    h, w = brightest.shape
    dark = brightest <= DARK
    rows, cols = dark.mean(axis=1) >= BAR, dark.mean(axis=0) >= BAR
    margin = max(int(MARGIN * h), 1)

    def extent(flags):  # black rows/columns running in from one edge, plus BORDER
        run = len(flags) if flags.all() else int(np.argmin(flags))
        return max(run + BORDER if run else 0, margin)

    zone = np.zeros((h, w), bool)
    zone[:extent(rows)] = True
    zone[h - extent(rows[::-1]):] = True
    zone[:, :extent(cols)] = True
    zone[:, w - extent(cols[::-1]):] = True
    return zone


def group(cand):
    """Split candidate pixels into separate candidates (8-connected BLOCK-px cells)."""
    h, w = cand.shape
    cand = cand.copy()
    cand[cand.mean(axis=1) >= LINE] = False
    cand[:, cand.mean(axis=0) >= LINE] = False
    gh, gw = -(-h // BLOCK), -(-w // BLOCK)
    padded = np.zeros((gh * BLOCK, gw * BLOCK), bool)
    padded[:h, :w] = cand
    cells = padded.reshape(gh, BLOCK, gw, BLOCK).sum(axis=(1, 3)) >= 3
    labels = np.zeros((gh, gw), int)
    n = 0
    for cy, cx in zip(*np.nonzero(cells)):
        if labels[cy, cx]:
            continue
        n += 1
        labels[cy, cx] = n
        stack = [(cy, cx)]
        while stack:
            y, x = stack.pop()
            for yy in range(max(y - 1, 0), min(y + 2, gh)):
                for xx in range(max(x - 1, 0), min(x + 2, gw)):
                    if cells[yy, xx] and not labels[yy, xx]:
                        labels[yy, xx] = n
                        stack.append((yy, xx))
    full = labels.repeat(BLOCK, 0).repeat(BLOCK, 1)[:h, :w]
    groups = []
    for k in range(1, n + 1):
        m = cand & (full == k)
        ys, xs = np.nonzero(m)
        if len(ys) >= MIN_PIXELS and min(np.ptp(ys), np.ptp(xs)) + 1 >= MIN_SIDE:
            groups.append(m)
    return groups


# ---------------------------------------------------------------------------
# Pass 2: when each candidate is on screen, and what exactly to mask
# ---------------------------------------------------------------------------
def spans(score):
    """On-screen (start, end) times from per-frame presence scores."""
    s = np.asarray(score)
    if len(s) >= 3:  # 3-tap median: one odd frame neither starts nor breaks an appearance
        s = np.median(np.stack([np.r_[s[:1], s[:-1]], s, np.r_[s[1:], s[-1:]]]), axis=0)
    runs, start, on = [], None, False
    for i, v in enumerate(s):
        on = v >= (OFF if on else ON)
        if on and start is None:
            start = i
        elif not on and start is not None:
            runs.append([start / TRACK_FPS, i / TRACK_FPS])
            start = None
    if start is not None:
        runs.append([start / TRACK_FPS, len(s) / TRACK_FPS])
    merged = []
    for a, b in runs:
        if merged and a - merged[-1][1] <= BRIDGE:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged if b - a >= MIN_ON]


def track(path, info, groups):
    w, h = info["width"], info["height"]
    margin = FILL_R + GROW + 6
    cands = []
    for m in groups:
        ys, xs = np.nonzero(m)
        y0, y1 = max(ys.min() - margin, 0), min(ys.max() + margin + 1, h)
        x0, x1 = max(xs.min() - margin, 0), min(xs.max() + margin + 1, w)
        tmpl = m[y0:y1, x0:x1]
        shape = tmpl.shape
        cands.append({"box": (y0, y1, x0, x1), "tmpl": tmpl, "ring": dilate(tmpl, 6) & ~dilate(tmpl, 2),
                      "score": [], "n": 0, "ecount": np.zeros(shape, np.int32),
                      "s": np.zeros(shape, np.int64), "sq": np.zeros(shape, np.int64)})
    step = max(w // 64, 1)
    thumbs = []
    for _, rgb in frames(path, TRACK_FPS, w, h):
        thumbs.append(luma(rgb[::step, ::step]))
        for c in cands:
            y0, y1, x0, x1 = c["box"]
            crop = rgb[y0:y1, x0:x1]
            e = edges(crop)
            score = e[c["tmpl"]].mean() - e[c["ring"]].mean()
            c["score"].append(score)
            if score >= ON:
                y = luma(crop).astype(np.int64)
                c["n"] += 1
                c["ecount"] += e
                c["s"] += y
                c["sq"] += y * y
    thumbs = np.stack(thumbs).astype(np.float32) if thumbs else np.zeros((0, 1, 1), np.float32)
    return cands, thumbs


def build(cands, thumbs, w, h):
    """Turn tracked candidates into overlays: on-screen spans, mask, static flag."""
    found = []
    for c in cands:
        on = spans(c["score"])
        if not on or not c["n"]:
            continue
        keep = c["ecount"] >= KEEP_EDGE * c["n"]
        std = np.sqrt(np.maximum(c["sq"] / c["n"] - (c["s"] / c["n"]) ** 2, 0))
        m = dilate(keep | ((std < STABLE) & dilate(keep, FILL_R)), GROW)
        m = fill_holes(m, HOLE * w * h)
        mask = np.zeros((h, w), bool)
        y0, y1, x0, x1 = c["box"]
        mask[y0:y1, x0:x1] = m
        view = max(thumbs[int(a * TRACK_FPS):int(b * TRACK_FPS)].std(axis=0).mean() for a, b in on)
        found.append({"mask": mask, "spans": on, "static": bool(view < STATIC_VIEW)})
    return merge(found)


def merge(found):
    """Candidates with matching appearances are parts of one overlay (e.g. a logo's words)."""
    def same(a, b):
        return len(a) == len(b) and all(abs(p - q) <= SAME_SPAN for x, y in zip(a, b) for p, q in zip(x, y))
    overlays = []
    for f in found:
        for o in overlays:
            if o["static"] == f["static"] and same(o["spans"], f["spans"]):
                o["mask"] |= f["mask"]
                break
        else:
            overlays.append(f)
    return overlays


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def clock(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def padded(o):
    return [(max(a - PAD, 0), b + PAD) for a, b in o["spans"]]


def write_pgm(path, mask):
    h, w = mask.shape
    with open(path, "wb") as f:
        f.write(f"P5 {w} {h} 255\n".encode())
        f.write((mask * 255).astype(np.uint8).tobytes())


def removelogo_graph(overlays, workdir, at=None):
    """removelogo per overlay, enabled while it is on screen (or only those on screen at `at`)."""
    parts = []
    for k, o in enumerate(overlays, 1):
        mask_path = Path(workdir) / f"mask{k}.pgm"
        write_pgm(mask_path, o["mask"])
        if at is None:
            expr = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in padded(o))
            parts.append(f"removelogo=f={mask_path}:enable='{expr}'")
        elif any(a <= at <= b for a, b in padded(o)):
            parts.append(f"removelogo=f={mask_path}")
    return ",".join(parts)


def grab(src, t, w, h, graph=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src)]
    if graph:
        cmd += ["-vf", graph]
    cmd += ["-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def preview(src, info, overlays, workdir, out_png):
    """One row per overlay, mid-way through its longest appearance: masked area tinted red | result."""
    w, h = info["width"], info["height"]
    rows = []
    for o in overlays:
        a, b = max(o["spans"], key=lambda s: s[1] - s[0])
        t = (a + b) / 2
        before = grab(src, t, w, h).copy()
        tint = np.zeros((h, w), bool)
        for p in overlays:
            if any(x - PAD <= t <= y + PAD for x, y in p["spans"]):
                tint |= p["mask"]
        before[tint] = (before[tint] // 2 + np.array([127, 0, 0], np.uint8))
        rows.append(np.hstack([before, grab(src, t, w, h, removelogo_graph(overlays, workdir, at=t))]))
    sheet = Path(workdir) / "preview.ppm"
    img = np.vstack(rows)
    with open(sheet, "wb") as f:
        f.write(f"P6 {img.shape[1]} {img.shape[0]} 255\n".encode())
        f.write(img.tobytes())
    out_png.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(sheet), "-vf", "scale='min(1600,iw)':-2",
                    str(out_png)], check=True)


def parse_numbers(text):
    return {int(v) for v in text.split(",")} if text else set()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--detect-only", action="store_true", help="report and write the preview, no video")
    ap.add_argument("--skip", help="overlay numbers to leave alone, e.g. 2 or 2,3")
    ap.add_argument("--include", help="static-scene overlay numbers to remove anyway")
    ap.add_argument("-o", "--output-dir", help="default: next to the input")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--force", action="store_true", help="overwrite an existing output")
    args = ap.parse_args()

    src = Path(args.input).resolve()
    info = probe(str(src))
    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else src.parent
    out = out_dir / f"{src.stem} [delogo].mp4"
    if out.exists() and not args.force and not args.detect_only:
        sys.exit(f"Output exists: {out} (use --force to overwrite)")

    print(f"Pass 1/2: looking for fixed overlays in {src.name} ...")
    groups = group(find_candidates(src, info))
    print(f"Pass 2/2: tracking {len(groups)} candidate(s) ...")
    found = build(*track(src, info, groups), info["width"], info["height"])
    skip, include = parse_numbers(args.skip), parse_numbers(args.include)
    overlays = []
    for k, o in enumerate(found, 1):
        ys, xs = np.nonzero(o["mask"])
        times = ", ".join(f"{clock(a)}-{clock(b)}" for a, b in o["spans"])
        if k in skip:
            status = "skipped (--skip)"
        elif o["static"] and k not in include:
            status = f"NOT removed: only seen over a static scene, may be background (--include {k})"
        else:
            status = "remove"
            overlays.append(o)
        print(f"  {k}. x{xs.min()}-{xs.max()} y{ys.min()}-{ys.max()} ({o['mask'].sum()} px), "
              f"on screen {times}: {status}")
    if not overlays:
        print("Nothing to remove.")
        return

    with tempfile.TemporaryDirectory() as workdir:
        out_png = DATA_DIR / "previews" / f"{src.stem} [delogo].png"
        preview(src, info, overlays, workdir, out_png)
        print(f"Preview (masked area in red | result): {out_png}")
        if args.detect_only:
            return

        out_dir.mkdir(parents=True, exist_ok=True)
        color = []
        for key, flag in (("color_space", "-colorspace"), ("color_primaries", "-color_primaries"),
                          ("color_transfer", "-color_trc")):
            if key in info["color"]:
                color += [flag, info["color"][key]]
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-stats", "-y", "-i", str(src),
                        "-vf", removelogo_graph(overlays, workdir), "-map", "0:v:0", "-map", "0:a?",
                        "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
                        *color, "-c:a", "copy", "-movflags", "+faststart", str(out)], check=True)
    copy_tags(str(src), str(out))
    problems = verify(src, out)
    if problems:
        print(f"Created {out}, but verification FAILED: {'; '.join(problems)}")
        sys.exit(1)
    print(f"Created: {out} (verified: same frames, identical audio and tags)")


if __name__ == "__main__":
    main()
