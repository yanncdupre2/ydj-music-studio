#!/usr/bin/env python3
"""Phase 2: Interactive batch updater for Apple Music metadata.

Reads a recommendations JSON (with all 4 sources filled in) and presents
each track for a single-keypress decision: 1 (primary), 2 (alternate), S (skip).

Usage:
    python3 tag_tracks.py --input /tmp/recommendations.json
    python3 tag_tracks.py --input /tmp/recommendations.json --dry-run
"""
import argparse
import json
import os
import subprocess
import sys
import termios
import tty

# Allow imports from library-management/
sys.path.insert(0, os.path.dirname(__file__))

from sources.genre_mapper import YDJ_GENRES


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


def update_track_metadata(track_id, year, genre, artist=None, name=None):
    """Update year and/or genre in Apple Music via AppleScript. Returns True on success.

    Args:
        track_id: Database ID (legacy, kept for compatibility but artist+name preferred)
        year: Year to set (or None to skip)
        genre: Genre to set (or None to skip)
        artist: Artist name (optional, improves reliability)
        name: Track name (optional, improves reliability)
    """
    updates = []
    if year:
        updates.append(f'set year of targetTrack to {year}')
    if genre:
        # Escape double quotes in genre
        genre_escaped = genre.replace('"', '\\"')
        updates.append(f'set genre of targetTrack to "{genre_escaped}"')

    if not updates:
        return True

    update_commands = '\n        '.join(updates)

    # Try artist + name search first (more reliable), fallback to database ID
    if artist and name:
        # Escape quotes in artist and name
        artist_escaped = artist.replace('"', '\\"')
        name_escaped = name.replace('"', '\\"')

        script = f'''
        tell application "Music"
            try
                set targetTrack to (first track of library playlist 1 whose artist is "{artist_escaped}" and name is "{name_escaped}")
                {update_commands}
                return "success"
            on error errMsg
                -- Fallback to database ID if artist+name search fails
                try
                    set targetTrack to (first track of library playlist 1 whose database ID is {track_id})
                    {update_commands}
                    return "success"
                on error errMsg2
                    return "error: " & errMsg2
                end try
            end try
        end tell
        '''
    else:
        # Legacy: database ID only
        script = f'''
        tell application "Music"
            try
                set targetTrack to (first track of library playlist 1 whose database ID is {track_id})
                {update_commands}
                return "success"
            on error errMsg
                return "error: " & errMsg
            end try
        end tell
        '''

    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip() == "success"
    except subprocess.CalledProcessError:
        return False


def main():
    parser = argparse.ArgumentParser(description='Interactive batch tagger for Apple Music')
    parser.add_argument('--input', required=True, help='Recommendations JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without writing')
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        recommendations = json.load(f)

    total = len(recommendations)
    updated = 0
    skipped = 0
    errors = 0

    print(f"{'='*60}")
    print(f"BATCH TAGGER — {total} tracks")
    if args.dry_run:
        print("(DRY RUN — no changes will be written)")
    print(f"{'='*60}")

    for i, rec in enumerate(recommendations, 1):
        consensus = rec.get('consensus', {})
        year = consensus.get('year')
        primary = consensus.get('genre_primary')
        alternate = consensus.get('genre_alternate')
        confidence = consensus.get('confidence', '?')

        # Header line
        year_str = str(year) if year else '????'
        print(f"\n[{i}/{total}] {rec['artist']} - {rec['name']} | Year: {year_str} ({confidence})")

        # Options
        opt1 = primary or '(none)'
        line = f"  1: {opt1}"
        if alternate:
            line += f"  |  2: {alternate}"
        line += "  |  S: Skip"
        print(line)

        # Wait for keypress
        sys.stdout.write("  > ")
        sys.stdout.flush()
        while True:
            ch = getch().upper()
            if ch == '1' and primary:
                genre = primary
                break
            elif ch == '2' and alternate:
                genre = alternate
                break
            elif ch == 'S':
                genre = None
                break
            elif ch == '\x03':  # Ctrl-C
                print("\nAborted.")
                sys.exit(1)

        if ch == 'S':
            print("S — skipped")
            skipped += 1
            continue

        print(f"{ch} — {genre}")

        if args.dry_run:
            print(f"  (dry run) Would set year={year}, genre={genre}")
            updated += 1
        else:
            ok = update_track_metadata(rec['track_id'], year, genre)
            if ok:
                updated += 1
            else:
                print(f"  ERROR updating track {rec['track_id']}")
                errors += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"Done: {updated} updated, {skipped} skipped, {errors} errors")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
