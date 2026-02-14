#!/usr/bin/env python3
"""Source A: Apple Music fuzzy duplicate search.

Searches the Apple Music library for tracks matching a given artist/title,
returning metadata (year, genre) from duplicate entries.

CLI:  python3 sources/duplicates.py "Artist" "Title" "track_id"
Import: from sources.duplicates import find_duplicates
"""
import json
import re
import subprocess
import sys
from difflib import SequenceMatcher


def normalize_string(s):
    """Normalize string for fuzzy matching: lowercase, strip parens, punctuation."""
    s = s.lower()
    s = re.sub(r'\([^)]*\)', '', s)
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def fuzzy_match_score(s1, s2):
    """Calculate fuzzy match score between two strings (0.0 - 1.0)."""
    return SequenceMatcher(None, normalize_string(s1), normalize_string(s2)).ratio()


def run_applescript(script):
    """Execute AppleScript and return stdout."""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"AppleScript error: {e.stderr}")


def find_duplicates(artist, name, exclude_track_id):
    """Find duplicate tracks in the Apple Music library.

    Returns list of dicts with keys: track_id, name, artist, year, genre, match_score.
    Matches require >0.8 fuzzy similarity on both artist and title.
    """
    search_script = f'''
    tell application "Music"
        set searchResults to (search library playlist 1 for "{artist}")

        set matchList to {{}}
        repeat with aTrack in searchResults
            try
                set trackID to database ID of aTrack
                set trackName to name of aTrack
                set trackArtist to artist of aTrack

                try
                    set trackYear to year of aTrack
                on error
                    set trackYear to 0
                end try

                try
                    set trackGenre to genre of aTrack
                on error
                    set trackGenre to ""
                end try

                set trackData to (trackID as text) & "|" & trackName & "|" & trackArtist & "|" & (trackYear as text) & "|" & trackGenre
                set end of matchList to trackData
            end try
        end repeat

        set AppleScript's text item delimiters to linefeed
        return matchList as text
    end tell
    '''

    result = run_applescript(search_script)

    duplicates = []
    for line in result.split('\n'):
        if not line:
            continue
        parts = line.split('|')
        if len(parts) >= 5:
            track_id = parts[0]
            if track_id == str(exclude_track_id):
                continue

            artist_score = fuzzy_match_score(artist, parts[2])
            name_score = fuzzy_match_score(name, parts[1])

            if artist_score > 0.8 and name_score > 0.8:
                duplicates.append({
                    'track_id': track_id,
                    'name': parts[1],
                    'artist': parts[2],
                    'year': int(parts[3]) if parts[3] != '0' else None,
                    'genre': parts[4] if parts[4] else None,
                    'match_score': (artist_score + name_score) / 2
                })

    duplicates.sort(key=lambda x: x['match_score'], reverse=True)
    return duplicates


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python3 sources/duplicates.py <artist> <title> <track_id>")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]
    track_id = sys.argv[3]

    results = find_duplicates(artist, title, track_id)
    print(json.dumps(results, indent=2))
