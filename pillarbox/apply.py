#!/usr/bin/env python3
"""Convert library videos in place, keeping a -backup copy next to each.

For each video: copy the original to "<name>-backup<ext>" in the same folder,
convert it with widen.py, verify the result (same frame count, bit-identical
audio, identical tags), then rename the converted file over the original.
The path Apple Music knows never changes, so nothing needs re-importing.
Every outcome is appended to pillarbox/data/conversions.log (tab-separated:
time, status, category, original, backup, detail).

Mode per scan category (looked up in the scan cache; --mode overrides):
    letterbox-in-4x3   crop   widescreen picture cut out of the 4:3 frame
    pillarbox-4x3      crop   4:3 picture, no zoom, no stretch
    pillarbox-5x4      fill   squeezed PAL: shape corrected to 4:3, 5% zoom, non-linear fill

Usage:
    venv/bin/python pillarbox/apply.py VIDEO [VIDEO ...]
    venv/bin/python pillarbox/apply.py --restore VIDEO [VIDEO ...]   # put the backups back
    venv/bin/python pillarbox/apply.py --trash-backups VIDEO [VIDEO ...]  # once checked: backups to the Trash
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from scan import CACHE_PATH, DATA_DIR, file_key  # noqa: E402

LOG_PATH = DATA_DIR / "conversions.log"
MODES = {
    "letterbox-in-4x3": ["--mode", "crop"],
    "pillarbox-4x3": ["--mode", "crop"],
    "pillarbox-5x4": ["--mode", "fill", "--aspect", "4:3"],
}


def backup_path(path):
    return path.with_name(f"{path.stem}-backup{path.suffix}")


def log(status, category, path, detail=""):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write("\t".join([time.strftime("%Y-%m-%d %H:%M:%S"), status, category, str(path),
                           str(backup_path(path)), detail]) + "\n")


def trash(path):
    """Move to the macOS Trash without overwriting anything already there.

    /usr/bin/trash (macOS 14+) renames on name clashes and keeps Finder's Put Back;
    without it, move under a unique name."""
    if Path("/usr/bin/trash").exists():
        subprocess.run(["/usr/bin/trash", str(path)], check=True)
        return
    dest = Path.home() / ".Trash" / path.name
    if dest.exists():
        dest = dest.with_name(f"{path.stem} {time.strftime('%Y%m%d-%H%M%S')}{path.suffix}")
    shutil.move(str(path), str(dest))


def streams(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height,nb_frames,duration,start_time", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return {s["codec_type"]: s for s in json.loads(out)["streams"] if s["codec_type"] in ("video", "audio")}


def audio_md5(path):
    return subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a", "-c", "copy", "-f", "md5", "-"],
                          capture_output=True, text=True, check=True).stdout.strip()


def tags(path):
    from mutagen import MutagenError
    from mutagen.mp4 import MP4
    try:
        return dict(MP4(path).tags or {})
    except MutagenError:
        return None


def packets(path, stream, entries):
    """Packet rows actually read from the file (container header counts can disagree)."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries",
                          f"packet={entries}", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return [line.rstrip(",").split(",") for line in out.splitlines() if line.strip()]


def shown_frames(path):
    """Video packets a player displays. Skips pre-roll frames with negative timestamps
    (hidden by the edit list) and empty MPEG-4 Part 2 'not coded' placeholders; ffmpeg
    drops both, so a faithful re-encode legitimately has fewer frames."""
    def shown(pts, size):
        return (pts == "N/A" or float(pts) >= 0) and int(size) > 8
    return sum(shown(pts, size) for pts, size in packets(path, "v:0", "pts_time,size"))


def verify(original, converted):
    """Return a list of problems; empty means same shown frames, identical audio and tags."""
    a, b = streams(original), streams(converted)
    problems = []
    fa, fb = shown_frames(original), len(packets(converted, "v:0", "size"))
    if fa != fb:
        problems.append(f"shown frames {fa} -> {fb}")
    if abs(float(a["video"].get("duration", 0)) - float(b["video"].get("duration", 0))) > 0.1:
        problems.append("video duration differs")
    if "audio" in a:
        # every audio packet must carry over untouched: same timestamps, durations, sizes, bytes
        entries = "pts,dts,duration,size"
        if "audio" not in b or packets(original, "a:0", entries) != packets(converted, "a:0", entries):
            problems.append("audio packets differ")
        elif audio_md5(original) != audio_md5(converted):
            problems.append("audio data differs")
    if tags(original) != tags(converted):
        problems.append("tags differ")
    return problems


def cached_category(path):
    if not CACHE_PATH.exists():
        return None
    hit = json.loads(CACHE_PATH.read_text()).get(str(path))
    if hit and hit["key"] == file_key(str(path)):
        return hit["result"]["category"]
    return None


def convert(path, mode_override):
    category = cached_category(path) or "?"
    mode_args = ["--mode", mode_override] if mode_override else MODES.get(category)
    if mode_args is None:
        print(f"SKIP  no conversion defined for category '{category}' (pass --mode): {path}")
        return False
    backup = backup_path(path)
    if backup.exists():
        print(f"SKIP  backup already exists (converted before?): {path}")
        log("skipped", category, path, "backup exists")
        return False

    print(f"\n=== {path.name}  [{category} -> {mode_args[1]}]")
    # APFS clone: instant, and takes no extra space until the original is replaced
    if subprocess.run(["cp", "-c", "-p", str(path), str(backup)]).returncode != 0:
        shutil.copy2(path, backup)
    if backup.stat().st_size != path.stat().st_size:
        trash(backup)
        sys.exit(f"Backup copy is incomplete; stopped before touching {path}")

    converted = path.with_name(f"{path.stem} [{mode_args[1]}].mp4")
    if converted.exists():  # left over from an earlier failed attempt
        trash(converted)
    result = subprocess.run([sys.executable, str(HERE / "widen.py"), str(path), *mode_args])
    problems = ["widen.py failed"] if result.returncode != 0 or not converted.exists() else verify(path, converted)
    if problems:
        # the original was never touched; keep any converted file for inspection, drop the backup
        trash(backup)
        log("FAILED", category, path, "; ".join(problems))
        print(f"FAILED ({'; '.join(problems)}): original left untouched")
        return False

    v = streams(converted)["video"]
    os.replace(converted, path)
    detail = f"{mode_args[1]} -> {v['width']}x{v['height']}"
    log("converted", category, path, detail)
    print(f"OK    {detail}; original saved as {backup.name}")
    return True


def restore(path):
    backup = backup_path(path)
    if not backup.exists():
        print(f"SKIP  no backup for {path}")
        return
    if path.exists():
        trash(path)  # the converted version
    os.rename(backup, path)
    log("restored", "", path)
    print(f"RESTORED {path}")


def trash_backup(path):
    backup = backup_path(path)
    if not backup.exists():
        print(f"SKIP  no backup for {path}")
        return False
    if not path.exists() or path.stat().st_size == 0:
        print(f"SKIP  converted file missing, keeping the backup: {backup}")
        return False
    trash(backup)
    log("backup-trashed", "", path)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--mode", choices=["crop", "fill"], help="override the per-category mode")
    action = ap.add_mutually_exclusive_group()
    action.add_argument("--restore", action="store_true", help="move each converted file to the Trash "
                                                               "and rename its backup back")
    action.add_argument("--trash-backups", action="store_true", help="once checked: move each video's "
                                                                     "-backup to the Trash")
    args = ap.parse_args()

    paths = [Path(os.path.abspath(v)) for v in args.videos]
    for p in paths:
        if p.name.endswith(f"-backup{p.suffix}"):
            sys.exit(f"Pass the original name, not the backup: {p}")
    if args.restore:
        for p in paths:
            restore(p)
        return
    if args.trash_backups:
        done = sum(trash_backup(p) for p in paths)
        print(f"{done}/{len(paths)} backups moved to the Trash. Log: {LOG_PATH}")
        return
    done = sum(convert(p, args.mode) for p in paths)
    print(f"\n{done}/{len(paths)} converted. Log: {LOG_PATH}")


if __name__ == "__main__":
    main()
