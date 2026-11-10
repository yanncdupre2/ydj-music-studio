#!/usr/bin/env python3
"""Find music videos whose picture doesn't fill the 16:9 frame.

Scans the tracks of an Apple Music playlist (default: MASTER LIST DJ VIDEO).
For each video it reads the stream metadata, decodes a handful of frames
spread across the running time at low resolution, and measures how much of
the frame is real picture. A column only counts as bar if it is dark in every
sample, so dark scenes and fades don't trigger false hits. Side panels filled
with a blurred copy of the picture are flagged separately (low confidence).

Results are cached by path + size + mtime, so re-runs only scan new or
changed files. Outputs (gitignored):
    pillarbox/data/report.csv    one row per video, with the crop box
    pillarbox/data/report.html   thumbnails of every flagged video, detected
                                 picture area outlined in red

Usage:
    venv/bin/python pillarbox/scan.py                  # scan the default playlist
    venv/bin/python pillarbox/scan.py --rescan         # ignore the cache
    venv/bin/python pillarbox/scan.py FILE [FILE ...]  # scan specific files
"""

import argparse
import concurrent.futures
import csv
import hashlib
import html
import json
import os
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from urllib.parse import quote

import numpy as np

# ---------------------------------------------------------------------------
# Add project root so we can import common modules
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from common.apple_music import get_playlist_file_paths  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent / "data"
CACHE_PATH = DATA_DIR / "scan-cache.json"
DEFAULT_PLAYLIST = "MASTER LIST DJ VIDEO"
ANALYSIS_VERSION = 1    # bump when detection changes, to invalidate cached results

SAMPLES = 8             # frames per video, spread over 10%..90% of the running time
AW, AH = 640, 360       # analysis resolution; results are kept as fractions of the frame
DARK = 24               # full-range luma at or below which a pixel counts as black
PERCENTILE = 90         # a column is picture if its 90th-percentile luma beats DARK in any
                        # sample, so a logo covering <10% of a bar doesn't hide the bar
MIN_BAR = 0.02          # each bar must cover >= 2% of the frame (ignores capture-edge junk)
PAL_SQUEEZED = (1.20, 1.275)  # a 5:4 picture: 4:3 PAL that lost its pixel shape (1.25 +-2%)
PANEL_STEP = 1.6        # detail must jump >= 1.6x across a panel edge...
PANEL_RATIO = 0.6       # ...and the panel must carry < 60% of the centre's detail
PANEL_MIN = 0.05        # ...and be >= 5% of the width (thinner = capture-edge junk)
THUMB_H = 270

CATEGORIES = {
    "pillarbox-5x4": "Black side bars around a 5:4 picture: almost certainly a 4:3 video squeezed "
                     "~6% too narrow (like Aicha). Fill candidate; widen.py also corrects the shape.",
    "pillarbox-4x3": "Black side bars around a correctly shaped 4:3 picture. Fill candidate.",
    "letterbox-in-4x3": "A widescreen picture letterboxed inside a narrow (4:3) file, so a 16:9 screen "
                        "shows bars on all four sides. Fix by cropping only, no stretching.",
    "soft-sides": "Possible side panels without real picture: a blurred copy of the video, or a flat "
                  "non-black fill. Low confidence: check the thumbnail.",
    "pillarbox-other": "Black side bars around a picture of another shape (see aspect). Check before filling.",
    "pillarbox-vertical": "Black side bars around a portrait (phone) picture. Not suitable for stretching.",
    "native-narrow": "The file itself is narrower than 16:9 (e.g. 640x480); the player adds the bars.",
    "letterbox": "Black bars top and bottom only (widescreen picture). Usually fine as is.",
    "uncertain": "Too few non-black samples to judge.",
    "error": "ffprobe/ffmpeg could not read the file.",
    "missing": "No local file for this track.",
    "ok": "Picture fills the frame.",
}
FLAGGED = [c for c in CATEGORIES if c not in ("ok", "error", "missing")]


# ---------------------------------------------------------------------------
# Measurement (also used by widen.py)
# ---------------------------------------------------------------------------
def probe(path):
    """Return display geometry, duration and colour tags of the first video stream."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=codec_name,width,height,sample_aspect_ratio,color_space,color_primaries,"
         "color_transfer:stream_side_data=rotation:format=duration", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    if not data.get("streams"):
        raise ValueError("no video stream")
    s = data["streams"][0]
    w, h = s["width"], s["height"]
    try:
        n, d = (int(v) for v in s.get("sample_aspect_ratio", "1:1").split(":"))
        sar = Fraction(n, d) if n and d else Fraction(1)
    except ValueError:
        sar = Fraction(1)
    rotation = next((int(sd["rotation"]) for sd in s.get("side_data_list", []) if "rotation" in sd), 0)
    if abs(rotation) % 180 == 90:  # ffmpeg auto-rotates decoded frames, so report display orientation
        w, h, sar = h, w, 1 / sar
    return {
        "codec": s.get("codec_name"), "width": w, "height": h, "sar": sar,
        "dar": float(w * sar / h), "duration": float(data.get("format", {}).get("duration") or 0),
        "color": {k: s[k] for k in ("color_space", "color_primaries", "color_transfer")
                  if s.get(k) and s[k] != "unknown"},
    }


def sample_times(duration, samples=SAMPLES):
    return [duration * (0.1 + 0.8 * i / (samples - 1)) for i in range(samples)]


def sample_frames(path, duration, size=(AW, AH), samples=SAMPLES):
    """Decode one keyframe near each sample time as full-range gray, stacked (n, h, w)."""
    if duration <= 0:
        raise ValueError("unknown duration")
    w, h = size
    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    for t in sample_times(duration, samples):
        # keyframe seek (no decode-forward to the exact time) and one decoder thread:
        # we need one frame per input, and parallelism comes from scanning files concurrently
        cmd += ["-noaccurate_seek", "-ss", f"{t:.3f}", "-threads", "1", "-i", path]
    graph = "".join(f"[{i}:v]scale={w}:{h},format=gray[f{i}];" for i in range(samples))
    graph += "".join(f"[f{i}]" for i in range(samples)) + f"vstack=inputs={samples}"
    cmd += ["-filter_complex", graph, "-frames:v", "1", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    if len(raw) != samples * w * h:
        raise ValueError("could not decode sample frames")
    return np.frombuffer(raw, np.uint8).reshape(samples, h, w)


def find_bars(frames):
    """Return (lit_frames, (left, right, top, bottom)) bar sizes in pixels.

    Bars are None when fewer than 3 samples carry any picture."""
    lit = frames[frames.reshape(len(frames), -1).mean(axis=1) > 8]  # drop black/fade frames
    if len(lit) < 3:
        return lit, None
    cols = np.percentile(lit, PERCENTILE, axis=1).max(axis=0)
    rows = np.percentile(lit, PERCENTILE, axis=2).max(axis=0)
    picture_cols, picture_rows = np.flatnonzero(cols > DARK), np.flatnonzero(rows > DARK)
    if picture_cols.size == 0 or picture_rows.size == 0:
        return lit, None
    return lit, (int(picture_cols[0]), int(cols.size - 1 - picture_cols[-1]),
                 int(picture_rows[0]), int(rows.size - 1 - picture_rows[-1]))


def find_soft_sides(lit, top, bottom):
    """Return (left, right) widths in pixels of detail-free side panels, or None.

    Looks for a sharp step in detail at mirrored positions. Averaged over
    samples from different scenes, natural soft focus fades gradually, while
    a composited panel edge sits at the same column in every frame."""
    h, w = lit.shape[1:]
    region = lit[:, top:h - bottom].astype(np.int16)
    detail = np.abs(np.diff(region, axis=1)).mean(axis=(0, 1))  # vertical-gradient energy per column
    centre = np.median(detail[int(w * 0.3):int(w * 0.7)])
    if centre < 0.5:  # picture too flat to judge
        return None
    k = 6
    candidates = range(max(k, int(PANEL_MIN * w)), int(w * 0.4))

    def edge(d):  # strongest outer-to-inner detail step: (ratio, column)
        return max((d[x:x + k].mean() / max(d[x - k:x].mean(), 0.05), x) for x in candidates)

    (step_l, l), (step_r, r) = edge(detail), edge(detail[::-1])
    if min(step_l, step_r) < PANEL_STEP or abs(l - r) > 0.03 * w:
        return None
    if max(detail[:l].mean(), detail[w - r:].mean()) > PANEL_RATIO * centre:
        return None
    return l, r


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
def classify(info, frames):
    h, w = frames.shape[1:]
    lit, bars = find_bars(frames)
    result = {"dar": round(info["dar"], 3), "width": info["width"], "height": info["height"]}
    if bars is None:
        return {**result, "category": "uncertain"}
    left, right, top, bottom = bars
    tb = top >= MIN_BAR * h and bottom >= MIN_BAR * h
    if not tb:
        top = bottom = 0  # thin edge junk, not bars
    soft = None
    side = left >= MIN_BAR * w and right >= MIN_BAR * w
    if not side:
        left = right = 0
        soft = find_soft_sides(lit, top, bottom)
        if soft:
            left, right = soft
    fx, fy = (w - left - right) / w, (h - top - bottom) / h
    aspect = info["dar"] * fx / fy
    if soft:
        category = "soft-sides"
    elif side:
        category = ("pillarbox-vertical" if aspect < 1.0 else
                    "pillarbox-5x4" if PAL_SQUEEZED[0] <= aspect < PAL_SQUEEZED[1] else
                    "pillarbox-4x3" if PAL_SQUEEZED[1] <= aspect < 1.40 else
                    "pillarbox-other")
    elif info["dar"] < 1.6:
        category = "letterbox-in-4x3" if tb and aspect >= 1.6 else "native-narrow"
    elif tb:
        category = "letterbox"
    else:
        category = "ok"
    # crop box in source pixels (display orientation), rounded to even numbers
    sx, sy = info["width"] / w, info["height"] / h
    box = [2 * round(v / 2) for v in ((w - left - right) * sx, (h - top - bottom) * sy, left * sx, top * sy)]
    return {**result, "category": category, "aspect": round(aspect, 3), "windowbox": side and tb,
            "box": box, "frac": [left / w, right / w, top / h, bottom / h],
            "best": int(np.argmax(frames.reshape(len(frames), -1).mean(axis=1)))}


def make_thumb(path, info, result):
    """Save a colour thumbnail with the detected picture area outlined; return its file name."""
    tw = 2 * round(THUMB_H * info["dar"] / 2)
    left, right, top, bottom = result["frac"]
    box = (f"drawbox=x={left * tw:.0f}:y={top * THUMB_H:.0f}:w={(1 - left - right) * tw:.0f}:"
           f"h={(1 - top - bottom) * THUMB_H:.0f}:color=red@0.9:t=3")
    name = hashlib.sha1(path.encode()).hexdigest()[:16] + ".jpg"
    (DATA_DIR / "thumbs").mkdir(parents=True, exist_ok=True)
    t = sample_times(info["duration"])[result["best"]]
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-noaccurate_seek", "-ss", f"{t:.3f}",
                    "-i", path, "-frames:v", "1", "-vf", f"scale={tw}:{THUMB_H},setsar=1,{box}",
                    "-q:v", "4", str(DATA_DIR / "thumbs" / name)], capture_output=True, check=True)
    return name


def scan_file(path):
    try:
        info = probe(path)
        result = classify(info, sample_frames(path, info["duration"]))
        if result["category"] in FLAGGED and result["category"] != "uncertain":
            result["thumb"] = make_thumb(path, info, result)
        return result
    except (subprocess.CalledProcessError, ValueError, KeyError) as e:
        detail = e.stderr.decode(errors="replace") if isinstance(getattr(e, "stderr", None), bytes) else str(e)
        return {"category": "error", "error": detail.strip()[-300:]}


# ---------------------------------------------------------------------------
# Cache + reports
# ---------------------------------------------------------------------------
def file_key(path):
    st = os.stat(path)
    return [st.st_size, st.st_mtime_ns, ANALYSIS_VERSION]


def load_cache(rescan):
    if rescan or not CACHE_PATH.exists():
        return {}
    return json.loads(CACHE_PATH.read_text())


def save_cache(cache):
    tmp = CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache))
    tmp.replace(CACHE_PATH)


def write_csv(rows):
    with open(DATA_DIR / "report.csv", "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(["category", "artist", "name", "picture_aspect", "file_aspect", "width", "height",
                      "crop_w:h:x:y", "windowbox", "path", "error"])
        for t, r in rows:
            out.writerow([r["category"], t["Artist"], t["Name"], r.get("aspect", ""), r.get("dar", ""),
                          r.get("width", ""), r.get("height", ""),
                          ":".join(map(str, r["box"])) if r.get("box") else "", r.get("windowbox", ""),
                          t["Path"] or "", r.get("error", "")])


def write_html(rows, counts, source):
    sections = []
    for cat in FLAGGED + ["error", "missing"]:
        items = [(t, r) for t, r in rows if r["category"] == cat]
        if not items:
            continue
        cards = []
        for t, r in items:
            img = (f'<img src="thumbs/{r["thumb"]}" alt="" loading="lazy">' if r.get("thumb")
                   else '<div class="noimg">no thumbnail</div>')
            facts = []
            if "aspect" in r:
                facts.append(f'picture {r["aspect"]:.2f}:1 &middot; file {r["width"]}&times;{r["height"]} '
                             f'({r["dar"]:.2f}:1)')
            if r.get("windowbox"):
                facts.append("bars on all four sides")
            if r.get("box") and cat != "letterbox":
                facts.append(f'crop {":".join(map(str, r["box"]))}')
            if r.get("error"):
                facts.append(html.escape(r["error"]))
            link = f'<a href="file://{quote(t["Path"])}">{html.escape(t["Path"])}</a>' if t["Path"] else ""
            cards.append(f'<figure>{img}<figcaption><b>{html.escape(t["Artist"])} &ndash; '
                         f'{html.escape(t["Name"])}</b><span>{" &middot; ".join(facts)}</span>'
                         f'<small>{link}</small></figcaption></figure>')
        sections.append(f'<section><h2>{cat} <span class="n">{len(items)}</span></h2>'
                        f'<p>{html.escape(CATEGORIES[cat])}</p><div class="grid">{"".join(cards)}</div></section>')
    summary = "".join(f"<tr><td>{c}</td><td>{counts.get(c, 0)}</td></tr>" for c in CATEGORIES if counts.get(c))
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pillarbox Scan</title>
<style>
:root {{ --bg:#f7f7f5; --fg:#1d1d1f; --muted:#6e6e73; --card:#fff; --line:#e3e3e0; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#161618; --fg:#ececec; --muted:#9a9aa0; --card:#222225; --line:#333336; }} }}
body {{ margin:0; padding:24px 16px 48px; background:var(--bg); color:var(--fg);
       font:14px/1.45 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif; }}
main {{ max-width:1400px; margin:0 auto; }}
h1 {{ font-size:22px; margin:0 0 4px; }} h2 {{ font-size:17px; margin:32px 0 2px; }}
.n {{ color:var(--muted); font-weight:400; }} p {{ color:var(--muted); margin:0 0 12px; }}
table {{ border-collapse:collapse; margin-top:12px; }} td {{ padding:2px 16px 2px 0; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:14px; }}
figure {{ margin:0; background:var(--card); border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
img, .noimg {{ display:block; width:100%; aspect-ratio:16/9; object-fit:contain; background:#000; }}
.noimg {{ color:#888; display:grid; place-items:center; }}
figcaption {{ padding:8px 10px; display:grid; gap:2px; }} figcaption span {{ color:var(--muted); }}
small a {{ color:var(--muted); word-break:break-all; font-size:11px; }}
</style></head><body><main>
<h1>Pillarbox scan</h1><p>{html.escape(source)} &middot; {len(rows)} videos &middot; {time.strftime("%Y-%m-%d %H:%M")}</p>
<table>{summary}</table>{"".join(sections)}
</main></body></html>"""
    (DATA_DIR / "report.html").write_text(page)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="scan these files instead of the playlist")
    ap.add_argument("--playlist", default=DEFAULT_PLAYLIST)
    ap.add_argument("--rescan", action="store_true", help="ignore cached results")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    (DATA_DIR / "thumbs").mkdir(parents=True, exist_ok=True)
    if args.files:
        tracks = [{"Name": Path(f).stem, "Artist": "", "Path": os.path.abspath(f)} for f in args.files]
        source = f"{len(tracks)} file(s)"
    else:
        print(f"Reading playlist '{args.playlist}'...")
        listed = get_playlist_file_paths(args.playlist)
        seen, tracks = set(), []
        for t in listed:  # a track added to the playlist several times is reported once
            if t["Path"] is None or t["Path"] not in seen:
                seen.add(t["Path"])
                tracks.append(t)
        if len(tracks) < len(listed):
            print(f"{len(listed) - len(tracks)} duplicate playlist entries skipped")
        source = f"Playlist '{args.playlist}'"

    cache = load_cache(args.rescan)
    results, todo = {}, []
    for t in tracks:
        path = t["Path"]
        if not path or not os.path.exists(path):
            continue
        hit = cache.get(path)
        if hit and hit["key"] == file_key(path):
            results[path] = hit["result"]
        else:
            todo.append(path)
    print(f"{len(tracks)} tracks: {len(results)} cached, {len(todo)} to scan")

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(scan_file, p): p for p in todo}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            path = futures[fut]
            results[path] = fut.result()
            cache[path] = {"key": file_key(path), "result": results[path]}
            if i % 50 == 0 or i == len(todo):
                save_cache(cache)
                rate = i / (time.time() - start)
                print(f"  {i}/{len(todo)}  {rate:.1f} files/s  ~{(len(todo) - i) / rate:.0f}s left", flush=True)

    order = {c: i for i, c in enumerate(CATEGORIES)}
    rows = []
    for t in tracks:
        r = results.get(t["Path"]) if t["Path"] else None
        rows.append((t, r or {"category": "missing"}))
    rows.sort(key=lambda tr: (order[tr[1]["category"]], tr[0]["Artist"].lower(), tr[0]["Name"].lower()))
    counts = {}
    for _, r in rows:
        counts[r["category"]] = counts.get(r["category"], 0) + 1

    write_csv(rows)
    write_html(rows, counts, source)
    print()
    for c in CATEGORIES:
        if counts.get(c):
            print(f"  {c:20s} {counts[c]:5d}")
    print(f"\nReport: {DATA_DIR / 'report.html'}\nCSV:    {DATA_DIR / 'report.csv'}")


if __name__ == "__main__":
    main()
