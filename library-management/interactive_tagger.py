#!/usr/bin/env python3
"""
Interactive Tagger: 4-Source Metadata Tagging System

Uses 4 sources to determine genre and year for tracks missing metadata:
- Source A: Fuzzy duplicate matching (same artist/title in library)
- Source B: LLM knowledge base
- Source C: Web search
- Source D: MusicBrainz API

Maps external genres to 31 YDJ canonical genres via substring matching.
Provides interactive prompts with PRIMARY/ALTERNATE suggestions.
"""
import json
import os
import sys
import subprocess
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

# Add common module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load YDJ canonical genres
GENRES_PATH = os.path.join(os.path.dirname(__file__), '..', 'common', 'genres.json')
with open(GENRES_PATH, 'r') as f:
    YDJ_GENRES = json.load(f)


def normalize_string(s: str) -> str:
    """Normalize string for fuzzy matching: lowercase, remove special chars."""
    s = s.lower()
    # Remove content in parentheses (like "Video", "Remix", etc.)
    s = re.sub(r'\([^)]*\)', '', s)
    # Remove special characters and extra whitespace
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def fuzzy_match_score(s1: str, s2: str) -> float:
    """Calculate fuzzy match score between two strings (0.0 - 1.0)."""
    return SequenceMatcher(None, normalize_string(s1), normalize_string(s2)).ratio()


def run_applescript(script: str) -> str:
    """Execute AppleScript and return result."""
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


def find_duplicate_tracks(artist: str, name: str, exclude_track_id: str) -> List[Dict]:
    """
    Search Apple Music library for duplicate tracks (same artist/title).
    Returns list of matching tracks with their metadata.
    """
    # Search library for artist name
    search_script = f'''
    tell application "Music"
        set searchResults to (search library playlist 1 for "{artist}")

        set matchList to {{}}
        repeat with aTrack in searchResults
            try
                set trackID to database ID of aTrack
                set trackName to name of aTrack
                set trackArtist to artist of aTrack

                -- Get optional metadata
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
            track_name = parts[1]
            track_artist = parts[2]

            # Skip the track itself
            if track_id == exclude_track_id:
                continue

            # Fuzzy match on both artist and name
            artist_score = fuzzy_match_score(artist, track_artist)
            name_score = fuzzy_match_score(name, track_name)

            # Require high similarity (>0.8) for both artist and name
            if artist_score > 0.8 and name_score > 0.8:
                duplicates.append({
                    'track_id': track_id,
                    'name': track_name,
                    'artist': track_artist,
                    'year': int(parts[3]) if parts[3] != '0' else None,
                    'genre': parts[4] if parts[4] else None,
                    'match_score': (artist_score + name_score) / 2
                })

    # Sort by match score (highest first)
    duplicates.sort(key=lambda x: x['match_score'], reverse=True)
    return duplicates


def map_genre_to_ydj(external_genre: str) -> Optional[str]:
    """
    Map external genre to YDJ canonical genre via substring matching.
    Returns best matching YDJ genre or None if no good match.
    """
    if not external_genre:
        return None

    external_lower = external_genre.lower()

    # Try exact match first
    for ydj_genre in YDJ_GENRES:
        if external_lower == ydj_genre.lower():
            return ydj_genre

    # Try substring matching
    # Check if any YDJ genre component appears in external genre
    best_match = None
    best_score = 0.0

    for ydj_genre in YDJ_GENRES:
        # Split compound genre into components
        components = [c.strip().lower() for c in ydj_genre.split(',')]

        # Check if external genre contains any component
        for component in components:
            if component in external_lower or external_lower in component:
                score = len(component) / max(len(external_lower), len(component))
                if score > best_score:
                    best_score = score
                    best_match = ydj_genre

    # Return match if confidence is high enough (>0.5)
    return best_match if best_score > 0.5 else None


def get_musicbrainz_data(artist: str, title: str) -> Optional[Dict]:
    """
    Query MusicBrainz API for track metadata.
    Returns dict with 'year' and 'genres' or None if not found.
    """
    import urllib.parse
    import urllib.request
    import time

    # MusicBrainz requires User-Agent header
    headers = {
        'User-Agent': 'YDJMusicStudio/1.0 (https://github.com/yanncdupre2/ydj-music-studio)'
    }

    # Search for recording
    query = f'artist:"{artist}" AND recording:"{title}"'
    url = f'https://musicbrainz.org/ws/2/recording/?query={urllib.parse.quote(query)}&fmt=json&limit=3'

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Rate limiting: MusicBrainz allows 1 request per second
        time.sleep(1.0)

        recordings = data.get('recordings', [])
        if not recordings:
            return None

        # Use first result with highest score
        recording = recordings[0]

        # Extract year from release date
        year = None
        if 'releases' in recording and recording['releases']:
            release = recording['releases'][0]
            date_str = release.get('date', '')
            if date_str:
                year = int(date_str.split('-')[0])

        # Extract genres/tags
        genres = []
        for tag in recording.get('tags', []):
            tag_name = tag.get('name', '')
            if tag_name and tag.get('count', 0) > 0:
                genres.append(tag_name)

        return {
            'year': year,
            'genres': genres,
            'score': recording.get('score', 0)
        }

    except Exception as e:
        print(f"  [MusicBrainz] Error: {e}")
        return None


def determine_consensus(sources: Dict[str, Dict]) -> Dict:
    """
    Determine PRIMARY and ALTERNATE recommendations from all sources.

    sources format:
    {
        'duplicates': {'year': 2020, 'genre': 'Pop'},
        'llm': {'year': 2020, 'genre': 'Electronic'},
        'web': {'year': 2020, 'genre': 'EDM'},
        'musicbrainz': {'year': 2020, 'genre': 'House'}
    }

    Returns:
    {
        'year': 2020,  # Most common year
        'genre_primary': 'EDM, House, Techno',  # Mapped YDJ genre
        'genre_alternate': 'Electronic, Ambient, Experimental',  # Alternative if available
        'confidence': 'high' | 'medium' | 'low'
    }
    """
    # Collect all years
    years = []
    for source_data in sources.values():
        if source_data and source_data.get('year'):
            years.append(source_data['year'])

    # Most common year
    consensus_year = max(set(years), key=years.count) if years else None

    # Collect all genres and map to YDJ
    ydj_genres = []
    for source_name, source_data in sources.items():
        if source_data and source_data.get('genre'):
            genre = source_data['genre']
            # Handle MusicBrainz which returns list of genres
            if isinstance(genre, list):
                for g in genre:
                    mapped = map_genre_to_ydj(g)
                    if mapped:
                        ydj_genres.append(mapped)
            else:
                mapped = map_genre_to_ydj(genre)
                if mapped:
                    ydj_genres.append(mapped)

    # Find most common YDJ genre(s)
    if not ydj_genres:
        return {
            'year': consensus_year,
            'genre_primary': None,
            'genre_alternate': None,
            'confidence': 'low'
        }

    # Count occurrences
    genre_counts = {}
    for g in ydj_genres:
        genre_counts[g] = genre_counts.get(g, 0) + 1

    # Sort by count
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)

    primary = sorted_genres[0][0]
    alternate = sorted_genres[1][0] if len(sorted_genres) > 1 else None

    # Determine confidence
    if sorted_genres[0][1] >= 3:  # 3+ sources agree
        confidence = 'high'
    elif sorted_genres[0][1] >= 2:  # 2 sources agree
        confidence = 'medium'
    else:
        confidence = 'low'

    return {
        'year': consensus_year,
        'genre_primary': primary,
        'genre_alternate': alternate,
        'confidence': confidence
    }


def update_track_metadata(track_id: str, year: Optional[int], genre: Optional[str]) -> bool:
    """
    Update track metadata in Apple Music library.
    Returns True if successful.
    """
    updates = []
    if year:
        updates.append(f'set year of targetTrack to {year}')
    if genre:
        updates.append(f'set genre of targetTrack to "{genre}"')

    if not updates:
        return True  # Nothing to update

    update_commands = '\n        '.join(updates)

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

    result = run_applescript(script)
    return result == "success"


def display_track_info(track: Dict, sources: Dict, consensus: Dict):
    """Display track info and source recommendations."""
    print(f"\n{'='*80}")
    print(f"TRACK: {track['Artist']} - {track['Name']}")
    print(f"Track ID: {track['Track ID']}")
    print(f"{'='*80}")

    # Display source findings
    print("\nSOURCE FINDINGS:")
    print("-" * 80)

    # Source A: Duplicates
    dup_data = sources.get('duplicates')
    if dup_data:
        print(f"  [A] Duplicates: Year={dup_data.get('year', 'N/A')}, Genre={dup_data.get('genre', 'N/A')}")
    else:
        print(f"  [A] Duplicates: No matches found")

    # Source B: LLM
    llm_data = sources.get('llm')
    if llm_data:
        print(f"  [B] LLM Knowledge: Year={llm_data.get('year', 'N/A')}, Genre={llm_data.get('genre', 'N/A')}")
    else:
        print(f"  [B] LLM Knowledge: No data")

    # Source C: Web
    web_data = sources.get('web')
    if web_data:
        print(f"  [C] Web Search: Year={web_data.get('year', 'N/A')}, Genre={web_data.get('genre', 'N/A')}")
    else:
        print(f"  [C] Web Search: No data")

    # Source D: MusicBrainz
    mb_data = sources.get('musicbrainz')
    if mb_data:
        genres_str = ', '.join(mb_data.get('genres', [])) if mb_data.get('genres') else 'N/A'
        print(f"  [D] MusicBrainz: Year={mb_data.get('year', 'N/A')}, Genres={genres_str}")
    else:
        print(f"  [D] MusicBrainz: No data")

    # Display consensus
    print(f"\n{'='*80}")
    print(f"CONSENSUS (Confidence: {consensus['confidence'].upper()}):")
    print(f"{'='*80}")
    print(f"  Year: {consensus['year']}")
    print(f"  Genre (Primary): {consensus['genre_primary']}")
    if consensus['genre_alternate']:
        print(f"  Genre (Alternate): {consensus['genre_alternate']}")


def interactive_prompt(track: Dict, consensus: Dict) -> Tuple[Optional[int], Optional[str]]:
    """
    Prompt user for confirmation or manual selection.
    Returns (year, genre) tuple based on user choice.
    """
    # If high confidence and all data present, auto-confirm
    if consensus['confidence'] == 'high' and consensus['year'] and consensus['genre_primary']:
        print(f"\n✓ High confidence - Auto-setting metadata")
        return consensus['year'], consensus['genre_primary']

    # Otherwise, prompt user
    print(f"\nOPTIONS:")
    print(f"  [1] Primary: Year={consensus['year']}, Genre={consensus['genre_primary']}")
    if consensus['genre_alternate']:
        print(f"  [2] Alternate: Year={consensus['year']}, Genre={consensus['genre_alternate']}")
    print(f"  [S] Skip this track")
    print(f"  [M] Manual entry")

    while True:
        choice = input(f"\nSelect option (1/2/S/M): ").strip().upper()

        if choice == '1':
            return consensus['year'], consensus['genre_primary']
        elif choice == '2' and consensus['genre_alternate']:
            return consensus['year'], consensus['genre_alternate']
        elif choice == 'S':
            return None, None
        elif choice == 'M':
            # Manual entry
            year_input = input("Enter year (or blank to skip): ").strip()
            year = int(year_input) if year_input else None

            print("\nAvailable YDJ Genres:")
            for i, g in enumerate(YDJ_GENRES, 1):
                print(f"  {i:2}. {g}")

            genre_input = input("\nEnter genre number (or blank to skip): ").strip()
            if genre_input and genre_input.isdigit():
                idx = int(genre_input) - 1
                if 0 <= idx < len(YDJ_GENRES):
                    genre = YDJ_GENRES[idx]
                else:
                    genre = None
            else:
                genre = None

            return year, genre
        else:
            print("Invalid choice. Try again.")


def main():
    """Main interactive tagging workflow."""
    print("="*80)
    print("INTERACTIVE TAGGER: 4-Source Metadata Tagging System")
    print("="*80)

    # Load sample tracks
    sample_path = '/tmp/sample_tracks.json'
    if not os.path.exists(sample_path):
        print(f"\nError: Sample tracks file not found: {sample_path}")
        print("Please run the playlist reader script first to generate sample tracks.")
        return

    with open(sample_path, 'r') as f:
        tracks = json.load(f)

    print(f"\nLoaded {len(tracks)} sample tracks")
    print(f"\n{'='*80}")

    # Process each track
    for i, track in enumerate(tracks, 1):
        print(f"\n\n{'#'*80}")
        print(f"PROCESSING TRACK {i}/{len(tracks)}")
        print(f"{'#'*80}")

        artist = track['Artist']
        name = track['Name']
        track_id = track['Track ID']

        # Source A: Find duplicates
        print(f"\n[Source A] Searching for duplicate tracks...")
        duplicates = find_duplicate_tracks(artist, name, track_id)
        dup_source = None
        if duplicates:
            print(f"  Found {len(duplicates)} duplicate(s)")
            # Use best match
            best = duplicates[0]
            if best['year'] or best['genre']:
                dup_source = {
                    'year': best['year'],
                    'genre': best['genre']
                }
                print(f"  Best match: {best['artist']} - {best['name']}")
                print(f"    Year: {best['year']}, Genre: {best['genre']}")
        else:
            print(f"  No duplicates found")

        # Source B: LLM knowledge (placeholder - will be filled via web search or manual)
        print(f"\n[Source B] Checking LLM knowledge base...")
        print(f"  (Note: LLM knowledge will be supplemented by web search)")
        llm_source = None

        # Source C: Web search
        print(f"\n[Source C] Performing web search...")
        # This will be done via WebSearch tool in the next iteration
        # For now, placeholder
        web_source = None

        # Source D: MusicBrainz
        print(f"\n[Source D] Querying MusicBrainz API...")
        mb_data = get_musicbrainz_data(artist, name)
        mb_source = None
        if mb_data:
            print(f"  Score: {mb_data['score']}")
            print(f"  Year: {mb_data['year']}")
            print(f"  Genres: {', '.join(mb_data['genres']) if mb_data['genres'] else 'None'}")
            mb_source = {
                'year': mb_data['year'],
                'genre': mb_data['genres']
            }
        else:
            print(f"  No results found")

        # Collect all sources
        sources = {
            'duplicates': dup_source,
            'llm': llm_source,
            'web': web_source,
            'musicbrainz': mb_source
        }

        # Determine consensus
        consensus = determine_consensus(sources)

        # Display track info
        display_track_info(track, sources, consensus)

        # Interactive prompt
        year, genre = interactive_prompt(track, consensus)

        if year or genre:
            print(f"\nUpdating track...")
            print(f"  Year: {year}")
            print(f"  Genre: {genre}")

            success = update_track_metadata(track_id, year, genre)
            if success:
                print(f"  ✓ Update successful")
            else:
                print(f"  ✗ Update failed")
        else:
            print(f"\n⊘ Skipped")

    print(f"\n\n{'='*80}")
    print(f"TAGGING COMPLETE")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
