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

#: Record separator used to join AppleScript lists. ASCII 0x1F (unit separator)
#: is used rather than a printable character because track names, albums and
#: comments routinely contain "|", ",", and tabs.
SEP = "\x1f"


#: AppleScript renders an absent property as this literal when coerced to text.
MISSING = "missing value"


def _to_text(value):
    """Normalize an AppleScript text value, mapping an absent property to ""."""
    return "" if value == MISSING else value


def _to_int(value, zero_as_none=False):
    """Parse an AppleScript numeric string, tolerating "", "missing value" and floats."""
    text = (value or "").strip()
    if not text or text == MISSING:
        return None if zero_as_none else 0
    try:
        number = int(float(text))
    except ValueError:
        return None if zero_as_none else 0
    if number == 0 and zero_as_none:
        return None
    return number


def _to_duration_ms(value):
    """Convert an AppleScript duration in seconds to integer milliseconds."""
    text = (value or "").strip()
    if not text or text == MISSING:
        return 0
    try:
        return int(float(text) * 1000)
    except ValueError:
        return 0


#: (DataFrame column, AppleScript property, parser). One bulk AppleScript call
#: is made per entry, so cost scales with the number of FIELDS, not tracks.
TRACK_FIELDS = (
    ("Track ID", "database ID", lambda v: v.strip()),
    ("Name", "name", _to_text),
    ("Artist", "artist", _to_text),
    ("Album", "album", _to_text),
    ("Album Artist", "album artist", _to_text),
    ("Genre", "genre", _to_text),
    ("Year", "year", lambda v: _to_int(v, zero_as_none=True)),
    ("BPM", "bpm", _to_int),
    ("Rating", "rating", _to_int),
    ("Comments", "comment", _to_text),
    ("Grouping", "grouping", _to_text),
    ("Kind", "kind", _to_text),
    ("Play Count", "played count", _to_int),
    ("Duration (ms)", "duration", _to_duration_ms),
)


def _bulk_property(container_clause, prop):
    """Read one property across every track of a container in a single Apple Event.

    Asking for `<prop> of every track` returns the whole column in one event.
    Reading track-by-track costs one Apple Event *per property per track*, which
    is ~267,000 events for a 19k-track library and takes tens of minutes.
    """
    script = f'''
    tell application "Music"
        set oldD to AppleScript's text item delimiters
        set AppleScript's text item delimiters to (character id 31)
        set r to ({prop} of every track of {container_clause}) as text
        set AppleScript's text item delimiters to oldD
        return r
    end tell
    '''
    # Deliberately not run_applescript(): it calls .strip(), and Python counts
    # \x1c-\x1f as whitespace, so a trailing run of separators (every track
    # whose value is empty, e.g. 2,252 of 2,361 tracks with no album) would be
    # stripped and silently shorten this column. Strip only the newline.
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"AppleScript error reading {prop}: {e.stderr}")
    raw = result.stdout.rstrip("\n")
    return raw.split(SEP) if raw else []


def _fetch_tracks_bulk(container_clause, expected_count=None, progress=True):
    """Fetch all tracks of a container as dicts, one bulk call per field."""
    columns = {}
    for index, (column, prop, _) in enumerate(TRACK_FIELDS, 1):
        if progress:
            print(f"  [{index}/{len(TRACK_FIELDS)}] reading {prop}...", flush=True)
        columns[column] = _bulk_property(container_clause, prop)

    lengths = {col: len(vals) for col, vals in columns.items()}
    count = max(lengths.values()) if lengths else 0
    # Every column must have one entry per track. A short column means a value
    # contained the separator and desynced that field, which would silently
    # attach one track's metadata to another. Refuse rather than return skew.
    mismatched = {col: n for col, n in lengths.items() if n != count}
    if mismatched:
        raise RuntimeError(
            f"Bulk read desynced: expected {count} values per field, got {mismatched}"
        )
    if expected_count is not None and count != expected_count:
        raise RuntimeError(
            f"Bulk read returned {count} tracks, but the container reports {expected_count}"
        )

    parsers = {column: parser for column, _, parser in TRACK_FIELDS}
    return [
        {column: parsers[column](columns[column][i]) for column in columns}
        for i in range(count)
    ]


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
    LEGACY per-track reader. Retained for compatibility; not used by
    load_library_from_music_app(), which now uses the bulk path. This costs one
    Apple Event per property per track and is orders of magnitude slower.

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
                    set trackKind to kind of aTrack
                on error
                    set trackKind to ""
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
                    trackComments & "|" & trackGrouping & "|" & trackKind & "|" & ¬
                    (trackPlayCount as text) & "|" & (trackDuration as text)

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
            if len(parts) >= 14:
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
                        'Kind': parts[11],
                        'Play Count': int(parts[12]) if parts[12] else 0,
                        'Duration (ms)': int(float(parts[13]) * 1000) if parts[13] else 0  # Convert seconds to ms
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
        batch_size (int): Ignored. Retained for API compatibility; the reader
            now issues one bulk AppleScript call per field, not per batch.
        progress (bool): Show progress messages (default: True)

    Returns:
        pd.DataFrame: DataFrame with all library tracks
    """
    if progress:
        print("Reading library from Music app...")

    total_tracks = get_track_count()
    if progress:
        print(f"Total tracks in library: {total_tracks:,}")

    all_tracks = _fetch_tracks_bulk(
        "library playlist 1", expected_count=total_tracks, progress=progress
    )

    if progress:
        print(f"✓ Loaded {len(all_tracks):,} tracks from Music app")

    return pd.DataFrame(all_tracks)


def get_playlist_track_count(playlist_name: str) -> int:
    """Return the number of tracks in a named Music.app playlist (including smart playlists)."""
    escaped = playlist_name.replace('"', '\\"')
    script = f'''
    tell application "Music"
        count of tracks of user playlist "{escaped}"
    end tell
    '''
    return int(run_applescript(script))


def get_playlist_tracks_batch(playlist_name: str, start_index: int, batch_size: int = 100) -> list:
    """LEGACY per-track reader for a named playlist; superseded by the bulk path.

    Retained for compatibility. Same fields as get_tracks_batch, same slowness.
    """
    escaped = playlist_name.replace('"', '\\"')
    script = f'''
    tell application "Music"
        set pl to user playlist "{escaped}"
        set trackList to {{}}
        set endIndex to {start_index + batch_size - 1}

        repeat with i from {start_index} to endIndex
            try
                set aTrack to track i of pl

                set trackID to database ID of aTrack
                set trackName to name of aTrack
                set trackArtist to artist of aTrack

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
                    set trackKind to kind of aTrack
                on error
                    set trackKind to ""
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

                set trackData to (trackID as text) & "|" & trackName & "|" & trackArtist & "|" & ¬
                    trackAlbum & "|" & trackAlbumArtist & "|" & trackGenre & "|" & ¬
                    (trackYear as text) & "|" & (trackBPM as text) & "|" & (trackRating as text) & "|" & ¬
                    trackComments & "|" & trackGrouping & "|" & trackKind & "|" & ¬
                    (trackPlayCount as text) & "|" & (trackDuration as text)

                set end of trackList to trackData
            on error
                exit repeat
            end try
        end repeat

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
            if len(parts) >= 14:
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
                        'Kind': parts[11],
                        'Play Count': int(parts[12]) if parts[12] else 0,
                        'Duration (ms)': int(float(parts[13]) * 1000) if parts[13] else 0,
                    }
                    tracks.append(track)
                except (ValueError, IndexError) as e:
                    print(f"Warning: Failed to parse track: {e}")
                    continue
        return tracks
    except RuntimeError as e:
        print(f"Error fetching playlist batch: {e}")
        return []


def load_playlist_from_music_app(playlist_name: str, batch_size: int = 100, progress: bool = True) -> 'pd.DataFrame':
    """Load all tracks from a named Music.app playlist in batches (fast; smart playlists supported).

    Args:
        playlist_name: Exact playlist name as it appears in Music.app (case-sensitive).
        batch_size: Ignored. Retained for API compatibility.
        progress: Print progress to stdout.

    Returns:
        DataFrame with the same columns as load_library_from_music_app.
    """
    if progress:
        print(f'Reading playlist "{playlist_name}" from Music.app...')

    total = get_playlist_track_count(playlist_name)
    if progress:
        print(f"  {total:,} tracks in playlist")

    escaped = playlist_name.replace('"', '\\"')
    all_tracks = _fetch_tracks_bulk(
        f'user playlist "{escaped}"', expected_count=total, progress=progress
    )

    if progress:
        print(f"✓ Loaded {len(all_tracks):,} tracks from \"{playlist_name}\"")

    return pd.DataFrame(all_tracks)


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
