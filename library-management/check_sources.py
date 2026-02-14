#!/usr/bin/env python3
"""Helper script to check duplicates and MusicBrainz for a specific track."""
import sys
import subprocess
import json
import re
import urllib.parse
import urllib.request
import time
from difflib import SequenceMatcher

def normalize_string(s):
    """Normalize string for fuzzy matching."""
    s = s.lower()
    s = re.sub(r'\([^)]*\)', '', s)
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def fuzzy_match_score(s1, s2):
    """Calculate fuzzy match score."""
    return SequenceMatcher(None, normalize_string(s1), normalize_string(s2)).ratio()

def run_applescript(script):
    """Execute AppleScript."""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"AppleScript error: {e.stderr}")

def find_duplicates(artist, name, exclude_track_id):
    """Find duplicate tracks in library."""
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
            if track_id == exclude_track_id:
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

def get_musicbrainz(artist, title):
    """Query MusicBrainz API."""
    headers = {
        'User-Agent': 'YDJMusicStudio/1.0 (https://github.com/yanncdupre2/ydj-music-studio)'
    }

    query = f'artist:"{artist}" AND recording:"{title}"'
    url = f'https://musicbrainz.org/ws/2/recording/?query={urllib.parse.quote(query)}&fmt=json&limit=3'

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        time.sleep(1.0)  # Rate limiting

        recordings = data.get('recordings', [])
        if not recordings:
            return None

        recording = recordings[0]

        year = None
        if 'releases' in recording and recording['releases']:
            release = recording['releases'][0]
            date_str = release.get('date', '')
            if date_str:
                year = int(date_str.split('-')[0])

        genres = [tag['name'] for tag in recording.get('tags', []) if tag.get('count', 0) > 0]

        return {
            'year': year,
            'genres': genres,
            'score': recording.get('score', 0)
        }

    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: check_sources.py <artist> <name> <track_id>")
        sys.exit(1)

    artist = sys.argv[1]
    name = sys.argv[2]
    track_id = sys.argv[3]

    print("SOURCE A: DUPLICATES")
    print("="*80)
    duplicates = find_duplicates(artist, name, track_id)
    if duplicates:
        print(f"Found {len(duplicates)} duplicate(s):")
        for i, dup in enumerate(duplicates[:3], 1):
            print(f"  {i}. {dup['artist']} - {dup['name']}")
            print(f"     Year: {dup['year']}, Genre: {dup['genre']}")
            print(f"     Match score: {dup['match_score']:.2f}")
    else:
        print("No duplicates found")

    print(f"\nSOURCE D: MUSICBRAINZ")
    print("="*80)
    mb_data = get_musicbrainz(artist, name)
    if mb_data:
        if 'error' in mb_data:
            print(f"Error: {mb_data['error']}")
        else:
            print(f"Score: {mb_data['score']}")
            print(f"Year: {mb_data.get('year', 'N/A')}")
            print(f"Genres: {', '.join(mb_data.get('genres', [])) if mb_data.get('genres') else 'N/A'}")
    else:
        print("No results found")
