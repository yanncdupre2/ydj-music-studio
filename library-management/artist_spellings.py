#!/usr/bin/env python3
"""Make each artist's name consistent across the Apple Music library.

The library spells some artists several ways ("MC Solaar" / "Mc Solaar",
"Tiësto" / "Tiesto"). This finds every such group across both the Artist and
Album Artist fields, lets you pick one spelling per artist, and writes it.

Steps (only apply and undo write to the library):
  scan     read every track's artist fields, group spellings that differ only by
           case, accents, spacing or Unicode encoding, and look each group up on
           MusicBrainz (cached). Writes data/artist_groups.json.
  review   one keypress per artist: pick a library spelling, MusicBrainz's, an
           accent-free one, or type your own. Decisions go to
           data/artist_decisions.json; nothing is written to the library. Needs
           a real terminal (raw keypresses), so run it in Terminal.app.
  apply    take a library backup, then change every Artist / Album Artist value
           that holds one of a decided group's spellings. Each change is checked
           against the current value first, journaled before it is made
           (data/artist_journal.jsonl, with the file's path before and after),
           and read back. --only limits it to some groups (a trial run).
  undo     put journaled values back, newest first.

Consent is given per artist in review, not per track: one keypress settles every
track of that artist. The backup and the journal are the safety net.

With "Keep Music Media folder organized" on, Music moves a file when the name
its folder is built from changes: Album Artist if set, else Artist; compilation
albums stay in "Compilations". Review shows, per choice, how many files would
move. Changes of case or Unicode encoding keep the same folder on a
case-insensitive APFS volume. VirtualDJ keys its entries (cue points) by path,
so it sees a moved file as a new song; the journal records every path before
and after. This tool never edits VirtualDJ's files: an outside edit of its
database.xml once made VirtualDJ discard it (see PLANNING.md).

Usage:
    venv/bin/python library-management/artist_spellings.py scan
    venv/bin/python library-management/artist_spellings.py review
    venv/bin/python library-management/artist_spellings.py apply [--only KEY ...] [--dry-run]
    venv/bin/python library-management/artist_spellings.py undo
"""

import argparse
import json
import os
import re
import subprocess
import sys
import termios
import time
import tty
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from common.load_from_music_app import _bulk_property, _to_text  # noqa: E402

DATA_DIR = HERE / "data"
GROUPS_PATH = DATA_DIR / "artist_groups.json"
DECISIONS_PATH = DATA_DIR / "artist_decisions.json"
JOURNAL_PATH = DATA_DIR / "artist_journal.jsonl"
MB_CACHE_PATH = DATA_DIR / "musicbrainz_artists.json"
LIBRARY = "library playlist 1"
FIELDS = {"artist": "artist", "album artist": "album artist"}
IGNORE = {"various artists"}
MB_HEADERS = {"User-Agent": "YDJMusicStudio/1.0 (https://github.com/yanncdupre2/ydj-music-studio)"}
MB_MIN_SCORE = 90
MB_RETRY_WAITS = (0, 5, 15)   # s before each retry after a failed lookup
SEP = "\x1f"
PLAIN_PUNCTUATION = str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
                                   "−": "-", "‘": "'", "’": "'", "“": '"', "”": '"'})


# ---------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------
def strip_accents(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def plain_punctuation(text):
    """Typographic hyphens, apostrophes and quotes as plain ASCII (MusicBrainz writes "a‐ha")."""
    return text.translate(PLAIN_PUNCTUATION)


def group_key(name):
    """Spellings with the same key are one artist: case, accents, spacing, encoding and
    typographic punctuation ignored."""
    return re.sub(r"\s+", " ", strip_accents(plain_punctuation(name))).strip().casefold()


def folder_key(name):
    """The folder Music files a name under, compared the way APFS compares names:
    Music replaces / : and some punctuation with _, and a trailing period."""
    folder = re.sub(r'[/:?*"<>|\\’]', "_", unicodedata.normalize("NFC", name.strip()))
    return re.sub(r"\.$", "_", folder).casefold()


# ---------------------------------------------------------------------------
# Library access
# ---------------------------------------------------------------------------
def read_tracks():
    """Every track's persistent ID, name, artist fields and compilation flag."""
    props = ("persistent ID", "name", "artist", "album artist", "compilation", "cloud status")
    cols = {p: _bulk_property(LIBRARY, p) for p in props}
    lengths = {p: len(v) for p, v in cols.items()}
    if len(set(lengths.values())) != 1:
        sys.exit(f"Bulk read desynced: {lengths}")
    return [{"pid": cols["persistent ID"][i].strip(), "name": _to_text(cols["name"][i]) or "",
             "artist": _to_text(cols["artist"][i]) or "", "album artist": _to_text(cols["album artist"][i]) or "",
             "compilation": cols["compilation"][i].strip() == "true",
             "subscription": cols["cloud status"][i].strip() == "subscription"}
            for i in range(lengths["name"])]


def osa(script):
    out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip())
    return out.stdout.rstrip("\n")


def as_literal(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def track_state(pid):
    """(path or "", artist, album artist) of one track, read live."""
    # POSIX path is a Standard Additions command: inside the Music tell block it is
    # sent to Music, which fails, so convert the location outside the block.
    out = osa(f'''
    tell application "Music"
        set t to (first track of library playlist 1 whose persistent ID is "{pid}")
        set loc to missing value
        try
            set loc to location of t
        end try
        set fields to (artist of t) & (character id 31) & (album artist of t)
    end tell
    set p to ""
    if loc is not missing value then set p to POSIX path of loc
    return p & (character id 31) & fields''')
    path, artist, album_artist = out.split(SEP)
    return path, artist, album_artist


def write_fields(pid, values):
    """Set the given fields of one track."""
    sets = "\n        ".join(f"set {FIELDS[f]} of t to {as_literal(v)}" for f, v in values.items())
    osa(f'''
    tell application "Music"
        set t to (first track of library playlist 1 whose persistent ID is "{pid}")
        {sets}
    end tell''')


# ---------------------------------------------------------------------------
# MusicBrainz
# ---------------------------------------------------------------------------
def musicbrainz_name(name, cache):
    """MusicBrainz's spelling of an artist whose name matches `name` (same group key), or None."""
    key = group_key(name)
    if key in cache:
        return cache[key]
    url = ("https://musicbrainz.org/ws/2/artist/?query="
           + urllib.parse.quote(f'artist:"{name}"') + "&fmt=json&limit=5")
    for wait in MB_RETRY_WAITS:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=MB_HEADERS), timeout=10) as r:
                artists = json.loads(r.read().decode("utf-8")).get("artists", [])
            break
        except OSError as e:  # 503 = MusicBrainz asking us to slow down
            error = e
            time.sleep(wait)
        finally:
            time.sleep(1.0)  # MusicBrainz rate limit: 1 request per second
    else:
        print(f"  MusicBrainz lookup failed for {name!r}: {error}")
        return None  # not cached, so the next scan retries it
    found = next((plain_punctuation(a["name"]) for a in artists
                  if a.get("score", 0) >= MB_MIN_SCORE and group_key(a["name"]) == key), None)
    cache[key] = found
    return found


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------
def build_groups(tracks):
    """{key: {spellings: {spelling: {field: count}}, folders: {spelling: n files filed under it}}}."""
    uses = defaultdict(lambda: defaultdict(Counter))
    for t in tracks:
        for field in FIELDS:
            value = t[field].strip()
            if value and group_key(value) not in IGNORE:
                uses[group_key(value)][value][field] += 1
    groups = {}
    for key, spellings in uses.items():
        if len(spellings) < 2:
            continue
        folders = Counter()  # spelling that names each file's folder, for tracks this group files
        for t in tracks:
            if t["compilation"]:
                continue
            filed_by = (t["album artist"] or t["artist"]).strip()
            if filed_by in spellings:
                folders[filed_by] += 1
        groups[key] = {"spellings": {s: dict(c) for s, c in spellings.items()}, "folders": dict(folders)}
    return groups


def moves(group, choice):
    """Files that would move to another folder if the group were renamed to `choice`."""
    return sum(n for s, n in group["folders"].items() if folder_key(s) != folder_key(choice))


def cmd_scan(_args):
    print("Reading the library (live)...")
    tracks = read_tracks()
    groups = build_groups(tracks)
    DATA_DIR.mkdir(exist_ok=True)
    cache = json.loads(MB_CACHE_PATH.read_text()) if MB_CACHE_PATH.exists() else {}
    print(f"{len(tracks)} tracks, {len(groups)} artists spelled several ways. Asking MusicBrainz...")
    for i, (key, g) in enumerate(sorted(groups.items()), 1):
        most_used = max(g["spellings"], key=lambda s: sum(g["spellings"][s].values()))
        g["musicbrainz"] = musicbrainz_name(most_used, cache)
        g["encoding_only"] = len({unicodedata.normalize("NFC", s) for s in g["spellings"]}) == 1
        if i % 10 == 0:
            MB_CACHE_PATH.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
            print(f"  {i}/{len(groups)}")
    MB_CACHE_PATH.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
    GROUPS_PATH.write_text(json.dumps(groups, indent=1, ensure_ascii=False))
    subs = sum(1 for t in tracks if t["subscription"] and any(group_key(t[f].strip()) in groups for f in FIELDS))
    print(f"Wrote {GROUPS_PATH}: {len(groups)} groups, "
          f"{sum(g['encoding_only'] for g in groups.values())} differing only in Unicode encoding.")
    if subs:
        print(f"{subs} of their tracks are Apple Music subscription tracks, which scripts can't edit.")


# ---------------------------------------------------------------------------
# review
# ---------------------------------------------------------------------------
def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save_decision(decisions, key, group, choice):
    decisions[key] = {"choice": choice, "spellings": sorted(group["spellings"]),
                      "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    DECISIONS_PATH.write_text(json.dumps(decisions, indent=1, ensure_ascii=False))


def describe_uses(counts):
    return ", ".join(f"{field} {n}" for field, n in counts.items())


def cmd_review(_args):
    groups = load_json(GROUPS_PATH, None)
    if groups is None:
        sys.exit("Run scan first.")
    decisions = load_json(DECISIONS_PATH, {})

    encoding = [k for k, g in groups.items() if g["encoding_only"] and k not in decisions]
    if encoding:
        print(f"{len(encoding)} artists are spelled identically but stored in two Unicode encodings:")
        print("  " + ", ".join(sorted(unicodedata.normalize("NFC", next(iter(groups[k]["spellings"])))
                                     for k in encoding)))
        print("Store each in the standard (composed) form? Nothing visible changes. [y/n] ", end="", flush=True)
        if getch().lower() == "y":
            for k in encoding:
                save_decision(decisions, k, groups[k], unicodedata.normalize("NFC", next(iter(groups[k]["spellings"]))))
        print()

    todo = sorted(k for k in groups if k not in decisions)
    for i, key in enumerate(todo, 1):
        g = groups[key]
        spellings = sorted(g["spellings"], key=lambda s: -sum(g["spellings"][s].values()))
        options = [(str(n), s) for n, s in enumerate(spellings, 1)]
        if g["musicbrainz"] and g["musicbrainz"] not in spellings:
            options.append(("m", g["musicbrainz"]))
        plain = strip_accents(spellings[0])
        if plain not in [s for _, s in options]:
            options.append(("a", plain))
        total = sum(sum(c.values()) for c in g["spellings"].values())
        print(f"\n[{i}/{len(todo)}] {spellings[0]}   ({total} field values)")
        for k, s in options:
            if k.isdigit():
                label = describe_uses(g["spellings"][s])
            else:
                label = "MusicBrainz" if k == "m" else "accent-free"
            n = moves(g, s)
            where = "files stay" if n == 0 else f"{n} file{'s' * (n > 1)} move"
            mb = "  <- MusicBrainz" if k.isdigit() and s == g["musicbrainz"] else ""
            print(f"  {k}. {s:40s} {label:32s} {where}{mb}")
        print("  t. type a name   s. skip   q. quit (decisions so far are saved)")
        while True:
            print("> ", end="", flush=True)
            c = getch().lower()
            print(c)
            picked = dict(options).get(c)
            if picked:
                save_decision(decisions, key, g, picked)
                break
            if c == "t":
                typed = input("name: ").strip()
                if typed:
                    save_decision(decisions, key, g, typed)
                    break
            elif c == "s":
                save_decision(decisions, key, g, None)
                break
            elif c in ("q", "\x03"):
                print(f"Saved {DECISIONS_PATH}")
                return
    chosen = sum(1 for d in decisions.values() if d["choice"])
    print(f"\nDone: {chosen} artists to rename, {len(decisions) - chosen} skipped. Saved {DECISIONS_PATH}")


# ---------------------------------------------------------------------------
# apply / undo
# ---------------------------------------------------------------------------
def journal(entry):
    DATA_DIR.mkdir(exist_ok=True)
    with open(JOURNAL_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_journal():
    return [json.loads(line) for line in JOURNAL_PATH.read_text().splitlines()] if JOURNAL_PATH.exists() else []


def planned_changes(tracks, decisions, only):
    """[(track, {field: new value})] for decided groups (optionally only some)."""
    by_spelling = {}
    for key, d in decisions.items():
        if d["choice"] and (not only or key in only):
            for s in d["spellings"]:
                by_spelling[s] = d["choice"]
    plan = []
    for t in tracks:
        values = {f: by_spelling[t[f].strip()] for f in FIELDS
                  if t[f].strip() in by_spelling and t[f] != by_spelling[t[f].strip()]}
        if values:
            plan.append((t, values))
    return plan


def cmd_apply(args):
    decisions = load_json(DECISIONS_PATH, {})
    only = {group_key(k) for k in args.only} if args.only else None
    if only and not only <= set(decisions):
        sys.exit(f"Not decided yet: {sorted(only - set(decisions))}")
    print("Reading the library (live)...")
    plan = planned_changes(read_tracks(), decisions, only)
    writable = [(t, v) for t, v in plan if not t["subscription"]]
    subs = [t for t, _ in plan if t["subscription"]]
    fields = sum(len(v) for _, v in writable)
    print(f"{fields} field values on {len(writable)} tracks to change"
          + (f"; {len(subs)} subscription tracks can't be edited by script" if subs else "") + ".")
    for t in subs:
        print(f"  by hand in Music: {t['artist']} - {t['name']}")
    if args.dry_run or not writable:
        for t, v in writable[:40]:
            print(f"  {t['artist']} - {t['name']}: " + ", ".join(f"{f} {t[f]!r} -> {n!r}" for f, n in v.items()))
        return
    if input("Back up the library and apply? [y/N] ").strip().lower() != "y":
        return
    backup = subprocess.run([sys.executable, str(HERE.parent / "common" / "library_backup.py"), "backup",
                             "--note", "before artist spellings" + (f" ({', '.join(sorted(only))})" if only else "")])
    if backup.returncode != 0:
        sys.exit("Backup failed; nothing changed.")

    done = failed = 0
    for t, values in writable:
        try:
            path, artist, album_artist = track_state(t["pid"])
            current = {"artist": artist, "album artist": album_artist}
            stale = [f for f in values if current[f] != t[f]]
            if stale:
                print(f"SKIP  changed since read ({', '.join(stale)}): {t['artist']} - {t['name']}")
                failed += 1
                continue
            entry = {"pid": t["pid"], "name": t["name"], "old": {f: t[f] for f in values},
                     "new": values, "path_before": path}
            journal({**entry, "status": "pending", "at": time.strftime("%Y-%m-%d %H:%M:%S")})
            write_fields(t["pid"], values)
            path_after, artist, album_artist = track_state(t["pid"])
            after = {"artist": artist, "album artist": album_artist}
            ok = all(after[f] == v for f, v in values.items())
            journal({**entry, "path_after": path_after, "status": "done" if ok else "MISMATCH",
                     "at": time.strftime("%Y-%m-%d %H:%M:%S")})
            moved = f"  (file moved: {path_after})" if path and path_after != path else ""
            print(f"{'OK  ' if ok else 'MISMATCH'}  {t['artist']} - {t['name']}{moved}")
            done += ok
            failed += not ok
        except RuntimeError as e:
            print(f"ERROR {t['artist']} - {t['name']}: {e}")
            failed += 1
    print(f"\n{done} tracks changed, {failed} not. Journal: {JOURNAL_PATH}")


def cmd_undo(_args):
    entries = read_journal()
    undone = {e["undo_of"] for e in entries if "undo_of" in e}
    todo = [(i, e) for i, e in enumerate(entries) if e.get("status") == "done" and i not in undone]
    if not todo:
        print("Nothing to undo.")
        return
    if input(f"Put back the old values on {len(todo)} tracks? [y/N] ").strip().lower() != "y":
        return
    for i, e in reversed(todo):
        path_before, artist, album_artist = track_state(e["pid"])
        current = {"artist": artist, "album artist": album_artist}
        if any(current[f] != v for f, v in e["new"].items()):
            print(f"SKIP  changed since: {e['name']}")
            continue
        write_fields(e["pid"], e["old"])
        path_after, _, _ = track_state(e["pid"])
        journal({"undo_of": i, "pid": e["pid"], "name": e["name"], "restored": e["old"],
                 "path_before": path_before, "path_after": path_after, "at": time.strftime("%Y-%m-%d %H:%M:%S")})
        print(f"UNDONE {e['name']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("scan", help="find artists spelled several ways (read-only)")
    sub.add_parser("review", help="pick one spelling per artist (writes decisions only)")
    a = sub.add_parser("apply", help="back up, then write the decided spellings")
    a.add_argument("--only", nargs="+", help="only these artists (any spelling), e.g. a trial run")
    a.add_argument("--dry-run", action="store_true", help="show the changes without writing")
    sub.add_parser("undo", help="put journaled values back")
    args = ap.parse_args()
    {"scan": cmd_scan, "review": cmd_review, "apply": cmd_apply, "undo": cmd_undo}[args.command](args)


if __name__ == "__main__":
    main()
