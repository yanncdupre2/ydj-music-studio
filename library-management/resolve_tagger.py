#!/usr/bin/env python3
"""Phase 2: Interactive inconsistency resolver.

Reads enriched inconsistency groups JSON and presents each group for
single-keypress resolution: Fix (apply consensus to all tracks),
Ignore (add all tracks to ignore playlist), or Skip.

Must run in a real Terminal (needs TTY for single-keypress input).

Usage:
    python3 resolve_tagger.py --input /tmp/inconsistency_groups.json
    python3 resolve_tagger.py --input /tmp/inconsistency_groups.json --dry-run
"""
import argparse
import json
import os
import sys
import termios
import tty

# Allow imports from library-management/ and parent
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tag_tracks import update_track_metadata
from common.apple_music import add_tracks_to_playlist, verify_track

IGNORE_PLAYLIST = "Ignore year or genre inconsistencies"


def getch():
    """Read a single character from stdin without waiting for Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def display_group(group, index, total):
    """Display an inconsistency group with its tracks and consensus."""
    consensus = group.get('consensus', {})
    year = consensus.get('year')
    primary = consensus.get('genre_primary')
    alternate = consensus.get('genre_alternate')
    confidence = consensus.get('confidence', '?')

    year_str = str(year) if year else '????'

    print(f"\n{'='*70}")
    print(f"[{index}/{total}]  {group['grouping_artist']} - {group['normalized_title']}")
    print(f"{'-'*70}")

    # Track table
    name_width = max(len(t['name']) for t in group['tracks'])
    name_width = min(name_width, 45)
    print(f"  {'Name':<{name_width}}  Year  Genre")
    for t in group['tracks']:
        name = t['name'][:name_width]
        yr = str(t['year']) if t['year'] else '    '
        genre = t['genre'] or ''
        print(f"  {name:<{name_width}}  {yr:<4}  {genre}")

    print(f"{'-'*70}")
    fields = ', '.join(group.get('inconsistent_fields', []))
    print(f"  Inconsistency: {fields}")
    print(f"  Consensus ({confidence.upper()}): Year={year_str}, Genre={primary or '(none)'}")
    print(f"{'-'*70}")


def apply_fix(group, year, genre, dry_run=False):
    """Apply consistent year and genre to ALL tracks in the group."""
    success = 0
    errors = 0
    for t in group['tracks']:
        # Verify track ID matches expected artist+name before any update
        matches, actual_artist, actual_name = verify_track(
            t['track_id'], t.get('artist', ''), t.get('name', '')
        )
        if not matches:
            print(f"  SKIPPED track {t['track_id']}: ID mismatch!")
            print(f"    Expected: {t.get('artist')} - {t.get('name')}")
            print(f"    Actual:   {actual_artist} - {actual_name}")
            errors += 1
            continue

        if dry_run:
            print(f"  (dry run) Would set track {t['track_id']}: year={year}, genre={genre}")
            success += 1
        else:
            ok = update_track_metadata(
                t['track_id'], year, genre,
                artist=t.get('artist'),
                name=t.get('name')
            )
            if ok:
                success += 1
            else:
                print(f"  ERROR updating track {t['track_id']} ({t['name']})")
                errors += 1
    return success, errors


def apply_ignore(group, dry_run=False):
    """Add all tracks in the group to the ignore playlist."""
    track_ids = [t['track_id'] for t in group['tracks']]
    if dry_run:
        print(f"  (dry run) Would add {len(track_ids)} tracks to '{IGNORE_PLAYLIST}'")
        return len(track_ids), 0
    return add_tracks_to_playlist(track_ids, IGNORE_PLAYLIST)


def main():
    parser = argparse.ArgumentParser(description='Interactive inconsistency resolver')
    parser.add_argument('--input', required=True, help='Inconsistency groups JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        groups = json.load(f)

    total = len(groups)
    fixed = 0
    ignored = 0
    skipped = 0
    errors = 0

    print(f"{'='*70}")
    print(f"INCONSISTENCY RESOLVER — {total} groups")
    if args.dry_run:
        print("(DRY RUN — no changes will be written)")
    print(f"{'='*70}")

    for i, group in enumerate(groups, 1):
        consensus = group.get('consensus', {})
        year = consensus.get('year')
        primary = consensus.get('genre_primary')
        alternate = consensus.get('genre_alternate')

        display_group(group, i, total)

        # Build options line
        opt1 = primary or '(none)'
        line = f"  1: {opt1}"
        if alternate:
            line += f"  |  2: {alternate}"
        line += "  |  I: Ignore  |  S: Skip"
        print(line)

        # Wait for keypress
        sys.stdout.write("  > ")
        sys.stdout.flush()
        while True:
            ch = getch().upper()
            if ch == '1' and primary:
                break
            elif ch == '2' and alternate:
                break
            elif ch == 'I':
                break
            elif ch == 'S':
                break
            elif ch == 'Q':
                print("Q — quit")
                print(f"\n{'='*70}")
                print(f"Partial: {fixed} fixed, {ignored} ignored, {skipped} skipped, {errors} errors")
                print(f"{'='*70}")
                sys.exit(0)
            elif ch == '\x03':  # Ctrl-C
                print("\nAborted.")
                sys.exit(1)

        if ch == 'S':
            print("S — skipped")
            skipped += 1
        elif ch == 'I':
            print("I — adding to ignore playlist")
            s, e = apply_ignore(group, dry_run=args.dry_run)
            ignored += 1
            errors += e
        elif ch in ('1', '2'):
            genre = primary if ch == '1' else alternate
            print(f"{ch} — fixing all tracks: year={year}, genre={genre}")
            s, e = apply_fix(group, year, genre, dry_run=args.dry_run)
            fixed += 1
            errors += e

    # Summary
    print(f"\n{'='*70}")
    print(f"Done: {fixed} fixed, {ignored} ignored, {skipped} skipped, {errors} errors")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
