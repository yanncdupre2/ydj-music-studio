#!/usr/bin/env python3
"""Phase 1: Batch research all tracks using automated sources.

Queries Source A (duplicates) and Source D (MusicBrainz) for every track in the
input file (or directly from an Apple Music smart playlist). Writes a
recommendations JSON with placeholder slots for Source B (LLM) and Source C
(web search) to be filled in by Claude.

Usage:
    python3 research_tracks.py --playlist "Genre of Year Blank"
    python3 research_tracks.py --input /tmp/tracks_to_tag.json
    python3 research_tracks.py --input /tmp/tracks.json --skip-duplicates
"""
import argparse
import json
import subprocess
import sys
import os

# Allow imports from library-management/
sys.path.insert(0, os.path.dirname(__file__))

from sources.duplicates import find_duplicates
from sources.musicbrainz import get_musicbrainz
from sources.genre_mapper import determine_consensus


def read_playlist(playlist_name):
    """Read tracks from an Apple Music playlist via AppleScript.

    Returns list of dicts with keys: track_id, artist, name.
    """
    script = f'''
    tell application "Music"
        set pl to user playlist "{playlist_name}"
        set trackList to {{}}
        repeat with aTrack in tracks of pl
            set tid to database ID of aTrack
            set tname to name of aTrack
            set tartist to artist of aTrack
            set end of trackList to (tid as text) & "|||" & tname & "|||" & tartist
        end repeat
        set AppleScript's text item delimiters to linefeed
        return trackList as text
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error reading playlist '{playlist_name}': {e.stderr}", file=sys.stderr)
        sys.exit(1)

    tracks = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('|||')
        if len(parts) == 3:
            tracks.append({
                'track_id': parts[0].strip(),
                'artist': parts[2].strip(),
                'name': parts[1].strip(),
            })
    return tracks


def research_track(track, skip_duplicates=False):
    """Research a single track using automated sources.

    Returns a recommendation dict with source_a through source_d slots.
    """
    artist = track['artist']
    name = track['name']
    track_id = str(track['track_id'])

    # Source A: Duplicates
    source_a = {'year': None, 'genre': None}
    if not skip_duplicates:
        try:
            duplicates = find_duplicates(artist, name, track_id)
            if duplicates:
                best = duplicates[0]
                source_a = {
                    'year': best.get('year'),
                    'genre': best.get('genre')
                }
        except Exception as e:
            print(f"  [A] Error: {e}", file=sys.stderr)

    # Source D: MusicBrainz
    source_d = {'year': None, 'genres': []}
    try:
        mb_data = get_musicbrainz(artist, name)
        if mb_data and 'error' not in mb_data:
            source_d = {
                'year': mb_data.get('year'),
                'genres': mb_data.get('genres', [])
            }
    except Exception as e:
        print(f"  [D] Error: {e}", file=sys.stderr)

    # Placeholders for Claude to fill
    source_b = {'year': None, 'genre': None}
    source_c = {'year': None, 'genre': None}

    # Compute initial consensus (will be recomputed after B+C are filled)
    sources = {
        'source_a': source_a,
        'source_b': source_b,
        'source_c': source_c,
        'source_d': source_d,
    }
    consensus = determine_consensus(sources)

    return {
        'track_id': track_id,
        'artist': artist,
        'name': name,
        'source_a': source_a,
        'source_b': source_b,
        'source_c': source_c,
        'source_d': source_d,
        'consensus': consensus,
    }


def main():
    parser = argparse.ArgumentParser(description='Batch research tracks for metadata tagging')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help='Input JSON file with tracks')
    group.add_argument('--playlist', help='Apple Music playlist name to read tracks from')
    parser.add_argument('--output', default='/tmp/recommendations.json', help='Output recommendations file')
    parser.add_argument('--skip-duplicates', action='store_true', help='Skip Source A (duplicate search)')
    args = parser.parse_args()

    if args.playlist:
        print(f"Reading tracks from playlist: {args.playlist}")
        tracks = read_playlist(args.playlist)
    else:
        with open(args.input, 'r') as f:
            tracks = json.load(f)

    print(f"Researching {len(tracks)} tracks...")
    if args.skip_duplicates:
        print("  (Skipping Source A: duplicate search)")

    recommendations = []
    for i, track in enumerate(tracks, 1):
        label = f"{track['artist']} - {track['name']}"
        print(f"\n[{i}/{len(tracks)}] {label}")

        if not args.skip_duplicates:
            print(f"  [A] Searching duplicates...")
        print(f"  [D] Querying MusicBrainz...")

        rec = research_track(track, skip_duplicates=args.skip_duplicates)
        recommendations.append(rec)

        # Show what we found
        a_year = rec['source_a']['year']
        a_genre = rec['source_a']['genre']
        d_year = rec['source_d']['year']
        d_genres = ', '.join(rec['source_d']['genres']) if rec['source_d']['genres'] else 'none'
        if not args.skip_duplicates:
            print(f"  [A] year={a_year}, genre={a_genre}")
        print(f"  [D] year={d_year}, genres={d_genres}")

    with open(args.output, 'w') as f:
        json.dump(recommendations, f, indent=2)

    print(f"\nDone. Wrote {len(recommendations)} recommendations to {args.output}")
    print("Next: Claude fills in source_b + source_c, then run tag_tracks.py")


if __name__ == '__main__':
    main()
