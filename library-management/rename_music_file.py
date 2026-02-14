#!/usr/bin/env python3
import os
import re
import sys
import tkinter as tk
from tkinter import filedialog
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp4 import MP4, MP4StreamInfoError

# -------- CONFIG --------
DRY_RUN = False  # set to False to actually rename
FILENAME_PATTERN = "{albumartist_or_artist} - {title}{year}{genre}{bpm_key}.mp3"  # extension will be adjusted to source ext
INCLUDE_YEAR_PARENS = True
INCLUDE_GENRE_BRACKETS = True
INCLUDE_BPM_KEY_BRACKETS = True

# Treat these as "Various Artists" and fall back to Artist
VA_ALIASES = {"various artists", "va", "varios artistas", "artistes variés", "divers", "divers artistes"}

# File types to process
EXTS_MP3 = {".mp3"}
EXTS_MP4 = {".mp4", ".m4a", ".m4v"}
EXTS = EXTS_MP3 | EXTS_MP4
# ------------------------


def sanitize_filename(name: str) -> str:
    name = name.replace("/", "-").replace(":", " -")
    name = re.sub(r"\s+", " ", name).strip()
    return name.rstrip(" .")


def ensure_unique_path(dirpath, filename):
    base, ext = os.path.splitext(filename)
    candidate = filename
    i = 1
    while os.path.exists(os.path.join(dirpath, candidate)):
        candidate = f"{base} ({i}){ext}"
        i += 1
    return candidate


# ---------------- MP3 helpers (ID3) ----------------
def easy_get(audio, key, default=""):
    vals = audio.get(key)
    if not vals:
        return default
    val = (vals[0] if isinstance(vals, list) else vals).strip()
    return val or default


def prefer_albumartist_id3(audio):
    albumartist = easy_get(audio, "albumartist", "")
    artist = easy_get(audio, "artist", "")
    if albumartist and albumartist.lower() not in VA_ALIASES:
        return albumartist
    return artist or "Unknown Artist"


def parse_year_id3(audio):
    date = easy_get(audio, "date", "")
    m = re.search(r"\b(\d{4})\b", date)
    return m.group(1) if m else ""


def read_tags_mp3(path):
    try:
        audio = EasyID3(path)
    except ID3NoHeaderError:
        return None  # no tags
    except Exception:
        return None

    data = {
        "artist": easy_get(audio, "artist", "Unknown Artist"),
        "albumartist": easy_get(audio, "albumartist", ""),
        "title": easy_get(audio, "title", "Unknown Title"),
        "album": easy_get(audio, "album", ""),
        "year_raw": parse_year_id3(audio),
        "genre_raw": easy_get(audio, "genre", ""),
        "bpm_raw": easy_get(audio, "bpm", ""),
        "key_raw": easy_get(audio, "initialkey", ""),
        "ext": ".mp3",
    }
    return data


# ---------------- MP4 helpers (M4A/MP4/M4V) ----------------
def mp4_get_first(tags, key, default=""):
    vals = tags.get(key)
    if not vals:
        return default
    val = vals[0]
    # tmpo (BPM) can be int; others are usually str
    return str(val).strip() if val is not None else default


def mp4_get_freeform(tags, name_list):
    """Look for freeform iTunes atoms like ----:com.apple.iTunes:initialkey"""
    for nm in name_list:
        vals = tags.get(nm)
        if vals:
            # MP4 freeform values are bytes; decode best-effort
            v = vals[0]
            if isinstance(v, bytes):
                try:
                    return v.decode("utf-8").strip()
                except Exception:
                    try:
                        return v.decode("latin-1").strip()
                    except Exception:
                        continue
            else:
                return str(v).strip()
    return ""


def prefer_albumartist_mp4(tags):
    albumartist = mp4_get_first(tags, "aART", "")
    artist = mp4_get_first(tags, "\xa9ART", "")
    if albumartist and albumartist.lower() not in VA_ALIASES:
        return albumartist
    return artist or "Unknown Artist"


def parse_year_mp4(tags):
    day = mp4_get_first(tags, "\xa9day", "")
    m = re.search(r"\b(\d{4})\b", day)
    return m.group(1) if m else ""


def read_tags_mp4(path):
    try:
        mp4 = MP4(path)
    except (MP4StreamInfoError, Exception):
        return None

    tags = mp4.tags or {}

    # Common atoms
    title = mp4_get_first(tags, "\xa9nam", "Unknown Title")
    artist = mp4_get_first(tags, "\xa9ART", "Unknown Artist")
    albumartist = mp4_get_first(tags, "aART", "")
    album = mp4_get_first(tags, "\xa9alb", "")
    year_raw = parse_year_mp4(tags)
    genre_raw = mp4_get_first(tags, "\xa9gen", "")
    bpm_val = tags.get("tmpo", [None])[0]
    bpm_raw = str(bpm_val) if bpm_val is not None else ""

    # Musical key: try several places (not standardized)
    key_candidates = [
        "----:com.apple.iTunes:initialkey",
        "----:com.apple.iTunes:INITIAL KEY",
        "----:com.apple.iTunes:Key",
        "----:com.apple.iTunes:KEY",
        "\xa9key",  # sometimes used
    ]
    key_raw = mp4_get_freeform(tags, key_candidates)

    data = {
        "artist": artist,
        "albumartist": albumartist,
        "title": title,
        "album": album,
        "year_raw": year_raw,
        "genre_raw": genre_raw,
        "bpm_raw": bpm_raw,
        "key_raw": key_raw,
        "ext": os.path.splitext(path)[1].lower(),  # keep original extension
    }
    return data


# ---------------- Formatting ----------------
def build_components_from_data(data):
    # Prefer albumartist except when it's a VA-like label
    albumartist_or_artist = (
        data.get("albumartist") or data.get("artist") or "Unknown Artist"
    )
    if albumartist_or_artist.lower() in VA_ALIASES:
        albumartist_or_artist = data.get("artist") or "Unknown Artist"

    title = data.get("title") or "Unknown Title"
    album = data.get("album", "")

    year = data.get("year_raw", "")
    genre = data.get("genre_raw", "")
    bpm = data.get("bpm_raw", "")
    initialkey = data.get("key_raw", "")

    year_seg = f" ({year})" if (INCLUDE_YEAR_PARENS and year) else ""
    genre_seg = f" [{genre}]" if (INCLUDE_GENRE_BRACKETS and genre) else ""

    inner = ", ".join(x for x in [(f"{bpm} BPM" if bpm else ""), (initialkey if initialkey else "")] if x)
    bpm_key_seg = f" [{inner}]" if (INCLUDE_BPM_KEY_BRACKETS and inner) else ""

    return {
        "artist": data.get("artist", "Unknown Artist"),
        "albumartist_or_artist": albumartist_or_artist,
        "album": album,
        "title": title,
        "year": year_seg,
        "genre": genre_seg,
        "bpm": bpm,
        "initialkey": initialkey,
        "bpm_key": bpm_key_seg,
        "ext": data.get("ext", ".mp3"),
    }


def rename_file(path):
    basename = os.path.basename(path)
    ext = os.path.splitext(basename)[1].lower()

    # Skip AppleDouble sidecars
    if basename.startswith("._"):
        # Quietly skip or print once:
        print(f"Skipping (AppleDouble): {basename}")
        return

    # Read tags according to type
    if ext in EXTS_MP3:
        data = read_tags_mp3(path)
    elif ext in EXTS_MP4:
        data = read_tags_mp4(path)
    else:
        return

    if data is None:
        print(f"Skipping (no readable tags): {basename}")
        return

    comps = build_components_from_data(data)
    new_filename = FILENAME_PATTERN.format(**comps)

    # Ensure correct extension matches the source file
    base_no_ext, _ = os.path.splitext(new_filename)
    new_filename = base_no_ext + comps["ext"]

    new_filename = sanitize_filename(new_filename)
    dirpath = os.path.dirname(path)
    new_filename = ensure_unique_path(dirpath, new_filename)
    new_path = os.path.join(dirpath, new_filename)

    if os.path.abspath(path) == os.path.abspath(new_path):
        print(f"Already named: {basename}")
        return

    if DRY_RUN:
        print(f"[DRY-RUN] {basename}  ->  {new_filename}")
    else:
        try:
            os.rename(path, new_path)
            print(f"Renamed: {basename}  ->  {new_filename}")
        except Exception as e:
            print(f"FAILED to rename {basename} -> {new_filename}: {e}")


def pick_folder():
    root = tk.Tk()
    root.withdraw()
    root.update()
    folder = filedialog.askdirectory(title="Choose a music folder")
    root.destroy()
    return folder


def main():
    print("Note: Processes MP3 (ID3) and MP4/M4A/M4V (MP4 atoms).")
    folder = pick_folder()
    if not folder:
        print("No folder selected. Exiting.")
        sys.exit(0)

    count = 0
    for dirpath, _, filenames in os.walk(folder):
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXTS:
                count += 1
                rename_file(os.path.join(dirpath, fn))

    print(f"Done. Processed {count} file(s).")
    if DRY_RUN:
        print("DRY-RUN was ON. Set DRY_RUN = False to actually rename.")


if __name__ == "__main__":
    main()
