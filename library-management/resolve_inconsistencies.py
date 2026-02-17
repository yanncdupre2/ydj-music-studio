#!/usr/bin/env python3
"""Phase 1: Detect inconsistency groups and research correct metadata.

Finds tracks with conflicting year/genre across variants (audio, video,
extended, remix), filters out tracks already in the "Ignore" playlist,
researches correct metadata via Source A (group majority) + Source D
(MusicBrainz), and writes a JSON for Claude to enrich with Sources B+C.

Usage:
    python3 resolve_inconsistencies.py
    python3 resolve_inconsistencies.py --output /tmp/inconsistency_groups.json
    python3 resolve_inconsistencies.py --all-library
"""
import argparse
import json
import sys
import os
from collections import Counter

# Allow imports from library-management/ and parent
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.apple_music import (
    load_playlist_from_app, get_playlist_track_ids_from_app,
    remove_accents, normalize_title
)
from sources.musicbrainz import get_musicbrainz
from sources.genre_mapper import determine_consensus
import pandas as pd

IGNORE_PLAYLIST = "Ignore year or genre inconsistencies"


def detect_inconsistency_groups(df):
    """Detect groups of tracks with inconsistent year or genre.

    Reuses cleanup.py's grouping logic: normalize titles, group by
    (Album Artist, Normalized Title), flag groups with multiple unique
    Year or Genre values.

    Returns:
        list[dict]: Groups with inconsistencies, sorted by most recent Date Added.
    """
    df = df.copy()
    df['Normalized Title'] = df['Name'].apply(normalize_title)
    df['Grouping Artist'] = df.apply(
        lambda row: remove_accents(row['Album Artist']) if str(row['Album Artist']).strip() != ""
        else remove_accents(row['Artist']),
        axis=1
    )
    df['Date Added'] = pd.to_datetime(df['Date Added'], errors='coerce')

    grouped = df.groupby(['Grouping Artist', 'Normalized Title'])
    groups = []

    for (group_artist, norm_title), group in grouped:
        unique_years = [y for y in group['Year'].unique() if y != '' and y != 0]
        unique_genres = [g for g in group['Genre'].unique() if g != '']

        inconsistent_fields = []
        if len(set(str(y) for y in group['Year'].unique())) > 1:
            inconsistent_fields.append('year')
        if len(group['Genre'].unique()) > 1:
            inconsistent_fields.append('genre')

        if not inconsistent_fields:
            continue

        tracks = []
        for _, row in group.iterrows():
            tracks.append({
                'name': row['Name'],
                'artist': row['Artist'],
                'track_id': str(row['Track ID']),
                'year': int(row['Year']) if row['Year'] != '' and row['Year'] != 0 else None,
                'genre': row['Genre'] if row['Genre'] != '' else None,
                'kind': row['Kind'],
            })

        groups.append({
            'grouping_artist': group_artist,
            'normalized_title': norm_title,
            'inconsistent_fields': inconsistent_fields,
            'tracks': tracks,
            'most_recent_date': group['Date Added'].max().isoformat() if pd.notna(group['Date Added'].max()) else None,
        })

    groups.sort(key=lambda x: x['most_recent_date'] or '', reverse=True)
    return groups


def filter_ignored_groups(groups, ignore_track_ids):
    """Remove groups where ALL tracks are already in the ignore playlist."""
    filtered = []
    for group in groups:
        group_track_ids = {t['track_id'] for t in group['tracks']}
        if not group_track_ids.issubset(ignore_track_ids):
            filtered.append(group)
    return filtered


def compute_source_a(group):
    """Compute Source A from the group's own tracks (majority year/genre)."""
    years = [t['year'] for t in group['tracks'] if t['year'] is not None]
    genres = [t['genre'] for t in group['tracks'] if t['genre'] is not None]

    majority_year = Counter(years).most_common(1)[0][0] if years else None
    majority_genre = Counter(genres).most_common(1)[0][0] if genres else None

    return {'year': majority_year, 'genre': majority_genre}


def research_group(group):
    """Research correct metadata for one inconsistency group.

    Computes Source A from group data, queries MusicBrainz for Source D.
    Sources B+C are placeholders for Claude.
    """
    artist = group['grouping_artist']
    title = group['normalized_title']

    # Source A: majority from group's own tracks
    source_a = compute_source_a(group)

    # Compute locked_fields: fields that are consistent should be preserved
    inconsistent = group.get('inconsistent_fields', [])
    locked_fields = {}
    if 'year' not in inconsistent and source_a['year'] is not None:
        locked_fields['year'] = source_a['year']
    if 'genre' not in inconsistent and source_a['genre'] is not None:
        locked_fields['genre'] = source_a['genre']
    group['locked_fields'] = locked_fields

    # Source D: MusicBrainz
    source_d = {'year': None, 'genres': []}
    try:
        mb_data = get_musicbrainz(artist, title)
        if mb_data and 'error' not in mb_data:
            source_d = {
                'year': mb_data.get('year'),
                'genres': mb_data.get('genres', [])
            }
    except Exception as e:
        print(f"  [D] Error: {e}", file=sys.stderr)

    # Placeholders for Claude
    source_b = {'year': None, 'genre': None}
    source_c = {'year': None, 'genre': None}

    # Initial consensus
    sources = {
        'source_a': source_a,
        'source_b': source_b,
        'source_c': source_c,
        'source_d': source_d,
    }
    consensus = determine_consensus(sources)

    # Override consensus with locked (consistent) fields
    if 'year' in locked_fields:
        consensus['year'] = locked_fields['year']
    if 'genre' in locked_fields:
        consensus['genre_primary'] = locked_fields['genre']
        consensus['genre_alternate'] = None

    group['source_a'] = source_a
    group['source_b'] = source_b
    group['source_c'] = source_c
    group['source_d'] = source_d
    group['consensus'] = consensus

    return group


def main():
    parser = argparse.ArgumentParser(description='Detect and research inconsistency groups')
    parser.add_argument('--output', default='/tmp/inconsistency_groups.json',
                        help='Output JSON file (default: /tmp/inconsistency_groups.json)')
    parser.add_argument('--all-library', action='store_true',
                        help='Analyze entire library instead of just DJ playlists')
    parser.add_argument('--playlist', type=str,
                        help='Analyze specific playlist by name')
    args = parser.parse_args()

    # Load tracks directly from Apple Music via AppleScript (no XML)
    if args.playlist:
        print(f"Loading playlist from Apple Music: {args.playlist}")
        df = load_playlist_from_app(args.playlist)
        source_desc = f'Playlist "{args.playlist}"'
    elif args.all_library:
        print("Loading DJ AUDIO + VIDEO from Apple Music (--all-library not supported without XML)...")
        df = load_playlist_from_app("DJ AUDIO + VIDEO")
        source_desc = "DJ AUDIO + VIDEO"
    else:
        print("Loading DJ AUDIO + VIDEO playlist from Apple Music...")
        df = load_playlist_from_app("DJ AUDIO + VIDEO")
        source_desc = "DJ AUDIO + VIDEO"

    # Detect groups
    groups = detect_inconsistency_groups(df)
    print(f"\nAnalyzing: {source_desc}")
    print(f"Total tracks: {len(df):,}")
    print(f"Groups with inconsistencies: {len(groups)}")

    # Filter out ignored groups (read from Apple Music directly)
    try:
        ignore_ids = get_playlist_track_ids_from_app(IGNORE_PLAYLIST)
        before = len(groups)
        groups = filter_ignored_groups(groups, ignore_ids)
        filtered = before - len(groups)
        if filtered > 0:
            print(f"Filtered out {filtered} already-ignored groups")
    except ValueError:
        print(f"Note: '{IGNORE_PLAYLIST}' playlist not found (will be created when needed)")

    if not groups:
        print("\nNo inconsistency groups to resolve!")
        return

    print(f"\nResearching {len(groups)} groups...")

    for i, group in enumerate(groups, 1):
        label = f"{group['grouping_artist']} - {group['normalized_title']}"
        print(f"\n[{i}/{len(groups)}] {label}")
        print(f"  Inconsistent: {', '.join(group['inconsistent_fields'])}")
        print(f"  Tracks: {len(group['tracks'])}")

        print(f"  [A] Group majority...")
        print(f"  [D] Querying MusicBrainz...")
        research_group(group)

        a = group['source_a']
        d = group['source_d']
        print(f"  [A] year={a['year']}, genre={a['genre']}")
        d_genres = ', '.join(d['genres']) if d['genres'] else 'none'
        print(f"  [D] year={d['year']}, genres={d_genres}")

    # Remove non-serializable fields
    for group in groups:
        group.pop('most_recent_date', None)

    with open(args.output, 'w') as f:
        json.dump(groups, f, indent=2)

    print(f"\nDone. Wrote {len(groups)} groups to {args.output}")
    print("Next: Claude fills in source_b + source_c, then run resolve_tagger.py")


if __name__ == '__main__':
    main()
