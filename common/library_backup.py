#!/usr/bin/env python3
"""Back up and restore the Apple Music library database.

How Music keeps its library (measured 2026-11-21, macOS 27): the database lives in
a background process, AMPLibraryAgent, not in Music.app. The agent keeps running
after Music quits, holds the library in memory and saves it to the package on
disk only now and then (most saves seen came right after Music launched). It
can't be controlled from a script: launchctl refuses to signal it, and a plain
SIGTERM sometimes makes it exit at once WITHOUT saving (an unsaved change was
lost in testing) and sometimes is ignored for minutes. So this tool never stops
it and never replaces files underneath it.

Backup copies the package as last saved, without quitting Music. Each file is an
APFS clone (instant, no extra space until the library changes; a plain copy where
cloning isn't available), and the copy only counts if the library's files are
identical before and after copying, so a save landing mid-copy can't produce a
mixed snapshot. The manifest records the size and SHA-256 of every file, when the
library was last saved (what the backup contains), and the track and playlist
counts Music showed at backup time (which can include unsaved changes).

Restore uses Music's own library switch, which makes the agent load the library
itself: the backup is checked against its manifest and cloned next to the current
library as "Music Library [restored NAME].musiclibrary"; you then hold Option
while opening Music, click Choose Library, and pick it. The current library is
left untouched, so going back is the same switch. `check` shows which library
Music uses now.

Not covered: media files (they live outside the package). With Sync Library
(iCloud) on, Music may re-apply changes from iCloud after switching to an older
library; to undo a script's metadata edits, prefer that script's own undo. Music's
own copies in "Previous Libraries" (made on major updates) are another fallback.

Usage:
    venv/bin/python common/library_backup.py backup [--note TEXT]
    venv/bin/python common/library_backup.py list
    venv/bin/python common/library_backup.py restore NAME   # NAME as shown by list
    venv/bin/python common/library_backup.py check          # which library Music uses
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

DEFAULT_LIBRARY = Path.home() / "Music" / "Music" / "Music Library.musiclibrary"
DATABASE = "Library.musicdb"
COPY_ATTEMPTS = 3      # a save landing mid-copy discards the copy; try again


def library_path():
    """The library Music opens, from its preferences (falls back to the default location)."""
    out = subprocess.run(["defaults", "read", "com.apple.Music", "library-url"],
                         capture_output=True, text=True)
    if out.returncode == 0 and out.stdout.strip():
        return Path(unquote(urlparse(out.stdout.strip()).path)).resolve()
    return DEFAULT_LIBRARY


def backup_root(library):
    return library.parent / "YDJ Library Backups"


def music_counts():
    """Track and playlist counts as Music shows them, or None if Music isn't running."""
    if subprocess.run(["pgrep", "-x", "Music"], capture_output=True).returncode != 0:
        return None
    out = subprocess.run(
        ["osascript", "-e", 'tell application "Music" to return ((count of tracks of library playlist 1) '
                            'as text) & "," & ((count of user playlists) as text)'],
        capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        return None
    tracks, playlists = (int(v) for v in out.stdout.strip().split(","))
    return {"tracks": tracks, "playlists": playlists}


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------
def fingerprint(package):
    """{relative path: {size, sha256}} for every file in the package."""
    files = {}
    for root, _, names in os.walk(package):
        for name in names:
            path = Path(root) / name
            digest = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    digest.update(chunk)
            files[str(path.relative_to(package))] = {"size": path.stat().st_size, "sha256": digest.hexdigest()}
    return files


def clone(src, dst):
    """Copy a directory tree, cloning each file on APFS (instant, no extra space until
    either side changes) and falling back to a plain copy file by file."""
    def clone_file(s, d):
        if subprocess.run(["cp", "-c", "-p", s, d], capture_output=True).returncode != 0:
            shutil.copy2(s, d)
        return d
    shutil.copytree(src, dst, symlinks=True, copy_function=clone_file)


def trash(path):
    """Move to the macOS Trash; /usr/bin/trash renames on clashes and keeps Put Back."""
    if Path("/usr/bin/trash").exists():
        subprocess.run(["/usr/bin/trash", str(path)], check=True)
        return
    dest = Path.home() / ".Trash" / path.name
    if dest.exists():
        dest = dest.with_name(f"{path.name} {time.strftime('%Y%m%d-%H%M%S')}")
    shutil.move(str(path), str(dest))


def saved_at(package):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime((package / DATABASE).stat().st_mtime))


def size_mb(manifest):
    return sum(f["size"] for f in manifest["files"].values()) / 1e6


def describe(manifest):
    c = manifest["counts"]
    shown = f"; Music showed {c['tracks']} tracks, {c['playlists']} playlists" if c else ""
    return f"library as saved {manifest['saved_at']}{shown}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_backup(args):
    library = library_path()
    counts = music_counts()
    dest = backup_root(library) / time.strftime("%Y-%m-%d %H.%M.%S")
    for _ in range(COPY_ATTEMPTS):
        before = fingerprint(library)
        dest.mkdir(parents=True)
        clone(library, dest / library.name)
        if fingerprint(dest / library.name) == before == fingerprint(library):
            break
        trash(dest)  # the library was saved while we copied
        time.sleep(2)
    else:
        sys.exit("The library kept changing while being copied; no backup made.")
    manifest = {"created": time.strftime("%Y-%m-%d %H:%M:%S"), "library": str(library),
                "saved_at": saved_at(library), "counts": counts, "note": args.note, "files": before}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"Backed up {library.name} ({size_mb(manifest):.0f} MB, {len(before)} files, verified) to: {dest}")
    print(f"  Contains the {describe(manifest)}.")
    print("  Changes made after that save are not in it (Music saves its library now and then).")


def cmd_list(_args):
    root = backup_root(library_path())
    names = sorted(p.name for p in root.iterdir() if (p / "manifest.json").exists()) if root.exists() else []
    if not names:
        print(f"No backups in {root}")
        return
    print(f"Backups in {root}:")
    for name in names:
        m = json.loads((root / name / "manifest.json").read_text())
        note = f"  [{m['note']}]" if m["note"] else ""
        print(f"  {name}  {size_mb(m):4.0f} MB  {describe(m)}{note}")


def cmd_restore(args):
    library = library_path()
    source_dir = backup_root(library) / args.name
    manifest_path = source_dir / "manifest.json"
    if not manifest_path.exists():
        sys.exit(f"No backup named '{args.name}' (see: list)")
    manifest = json.loads(manifest_path.read_text())
    package = source_dir / Path(manifest["library"]).name
    if fingerprint(package) != manifest["files"]:
        sys.exit("The backup no longer matches its manifest; not restoring from it.")
    target = library.parent / f"Music Library [restored {args.name}].musiclibrary"
    if target.exists():
        sys.exit(f"Already prepared: {target}")
    clone(package, target)
    if fingerprint(target) != manifest["files"]:
        trash(target)
        sys.exit("The prepared copy does not match the backup; removed it.")
    print(f"Backup {args.name} verified ({describe(manifest)}) and prepared as:\n  {target}\n")
    print("To switch Music to it:")
    print("  1. Quit Music.")
    print("  2. Hold Option while opening Music, click Choose Library, and select the file above.")
    print("  3. Run: venv/bin/python common/library_backup.py check")
    print(f"\nYour current library is untouched: {library}")
    print("To go back, do the same and select it instead.")


def cmd_check(_args):
    library = library_path()
    counts = music_counts()
    print(f"Music uses: {library}")
    print(f"  last saved {saved_at(library)}")
    if counts:
        print(f"  Music shows {counts['tracks']} tracks, {counts['playlists']} playlists")
    else:
        print("  (Music is not running)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    b = sub.add_parser("backup", help="clone the library as last saved into a new verified backup")
    b.add_argument("--note", default="", help="short description shown by list")
    sub.add_parser("list", help="list backups")
    r = sub.add_parser("restore", help="prepare a backup for Music's Choose Library switch")
    r.add_argument("name", help="backup name as shown by list")
    sub.add_parser("check", help="show which library Music uses")
    args = ap.parse_args()
    {"backup": cmd_backup, "list": cmd_list, "restore": cmd_restore, "check": cmd_check}[args.command](args)


if __name__ == "__main__":
    main()
