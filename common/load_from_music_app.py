#!/usr/bin/env python3
"""
Direct Apple Music Library Reader via AppleScript

Reads the library directly from the Music app (no XML export needed).
This ensures database IDs are always current and accurate.

Usage:
    from common.load_from_music_app import load_library_from_music_app

    df = load_library_from_music_app()
    # Returns pandas DataFrame with current library state
"""
import subprocess
import pandas as pd
from datetime import datetime


def run_applescript(script):
    """
    Execute AppleScript and return result.

    Args:
        script (str): AppleScript code to execute

    Returns:
        str: Output from AppleScript

    Raises:
        RuntimeError: If AppleScript execution fails
    """
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


def get_track_count():
    """
    Get total number of tracks in Music library.

    Returns:
        int: Number of tracks
    """
    script = '''
    tell application "Music"
        count of tracks of library playlist 1
    end tell
    '''
    result = run_applescript(script)
    return int(result)


def get_tracks_batch(start_index, batch_size=100):
    """
    Get a batch of tracks from Music library.

    Args:
        start_index (int): Starting index (1-based)
        batch_size (int): Number of tracks to fetch

    Returns:
        list: List of track dictionaries
    """
    script = f'''
    tell application "Music"
        set trackList to {{}}
        set endIndex to {start_index + batch_size - 1}

        repeat with i from {start_index} to endIndex
            try
                set aTrack to track i of library playlist 1

                -- Get basic info
                set trackID to database ID of aTrack
                set trackName to name of aTrack
                set trackArtist to artist of aTrack

                -- Get optional fields (may be missing)
                try
                    set trackAlbum to album of aTrack
                on error
                    set trackAlbum to ""
                end try

                try
                    set trackAlbumArtist to album artist of aTrack
                on error
                    set trackAlbumArtist to ""
                end try

                try
                    set trackGenre to genre of aTrack
                on error
                    set trackGenre to ""
                end try

                try
                    set trackYear to year of aTrack
                on error
                    set trackYear to 0
                end try

                try
                    set trackBPM to bpm of aTrack
                on error
                    set trackBPM to 0
                end try

                try
                    set trackRating to rating of aTrack
                on error
                    set trackRating to 0
                end try

                try
                    set trackComments to comment of aTrack
                on error
                    set trackComments to ""
                end try

                try
                    set trackGrouping to grouping of aTrack
                on error
                    set trackGrouping to ""
                end try

                try
                    set trackPlayCount to played count of aTrack
                on error
                    set trackPlayCount to 0
                end try

                try
                    set trackDuration to duration of aTrack
                on error
                    set trackDuration to 0
                end try

                -- Build delimited string for this track
                set trackData to (trackID as text) & "|" & trackName & "|" & trackArtist & "|" & ¬
                    trackAlbum & "|" & trackAlbumArtist & "|" & trackGenre & "|" & ¬
                    (trackYear as text) & "|" & (trackBPM as text) & "|" & (trackRating as text) & "|" & ¬
                    trackComments & "|" & trackGrouping & "|" & (trackPlayCount as text) & "|" & (trackDuration as text)

                set end of trackList to trackData
            on error
                -- Track doesn't exist (reached end of library)
                exit repeat
            end try
        end repeat

        -- Join all tracks with newline
        set AppleScript's text item delimiters to linefeed
        return trackList as text
    end tell
    '''

    try:
        result = run_applescript(script)
        if not result:
            return []

        tracks = []
        for line in result.split('\n'):
            if not line:
                continue

            parts = line.split('|')
            if len(parts) >= 13:
                try:
                    track = {
                        'Track ID': parts[0],
                        'Name': parts[1],
                        'Artist': parts[2],
                        'Album': parts[3],
                        'Album Artist': parts[4],
                        'Genre': parts[5],
                        'Year': int(parts[6]) if parts[6] and parts[6] != '0' else None,
                        'BPM': int(parts[7]) if parts[7] and parts[7] != '0' else 0,
                        'Rating': int(parts[8]) if parts[8] and parts[8] != '0' else 0,
                        'Comments': parts[9],
                        'Grouping': parts[10],
                        'Play Count': int(parts[11]) if parts[11] else 0,
                        'Duration (ms)': int(float(parts[12]) * 1000) if parts[12] else 0  # Convert seconds to ms
                    }
                    tracks.append(track)
                except (ValueError, IndexError) as e:
                    print(f"Warning: Failed to parse track: {e}")
                    continue

        return tracks
    except RuntimeError as e:
        print(f"Error fetching tracks: {e}")
        return []


def load_library_from_music_app(batch_size=100, progress=True):
    """
    Load entire Music library directly from Music app via AppleScript.

    Args:
        batch_size (int): Number of tracks to fetch per AppleScript call (default: 100)
        progress (bool): Show progress messages (default: True)

    Returns:
        pd.DataFrame: DataFrame with all library tracks
    """
    if progress:
        print("Reading library from Music app...")

    # Get total track count
    total_tracks = get_track_count()
    if progress:
        print(f"Total tracks in library: {total_tracks:,}")

    # Fetch tracks in batches
    all_tracks = []
    current_index = 1

    while current_index <= total_tracks:
        if progress:
            pct = (current_index / total_tracks) * 100
            print(f"  Fetching tracks {current_index:,}-{min(current_index + batch_size - 1, total_tracks):,} ({pct:.1f}%)...")

        batch = get_tracks_batch(current_index, batch_size)
        if not batch:
            break

        all_tracks.extend(batch)
        current_index += batch_size

    if progress:
        print(f"✓ Loaded {len(all_tracks):,} tracks from Music app")

    # Convert to DataFrame
    df = pd.DataFrame(all_tracks)
    return df


def main():
    """Test direct library loading."""
    print("Testing direct Music app library reader...\n")

    df = load_library_from_music_app()

    print(f"\n{'='*70}")
    print("LIBRARY LOADED FROM MUSIC APP")
    print(f"{'='*70}")
    print(f"\nTotal tracks: {len(df):,}")
    print(f"\nColumns: {', '.join(df.columns)}")

    print(f"\nSample tracks:")
    print(df[['Track ID', 'Name', 'Artist', 'Year', 'Genre']].head(10))

    # Check for missing metadata
    missing_year = df[df['Year'].isna()].shape[0]
    missing_genre = df[df['Genre'] == ''].shape[0]
    missing_bpm = df[df['BPM'] == 0].shape[0]

    print(f"\nMetadata completeness:")
    print(f"  Missing Year: {missing_year:,} ({missing_year/len(df)*100:.1f}%)")
    print(f"  Missing Genre: {missing_genre:,} ({missing_genre/len(df)*100:.1f}%)")
    print(f"  Missing BPM: {missing_bpm:,} ({missing_bpm/len(df)*100:.1f}%)")


if __name__ == "__main__":
    main()
