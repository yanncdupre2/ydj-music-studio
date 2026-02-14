import os
import re
import plistlib
import subprocess
import pandas as pd
import unicodedata

XML_LIBRARY_PATH = "~/YDJ Library.xml"

def load_raw_library():
    """
    Load the raw Apple Music library plist data.

    Returns:
        dict: Raw library data with 'Tracks' and 'Playlists' keys
    """
    path = os.path.expanduser(XML_LIBRARY_PATH)
    with open(path, 'rb') as f:
        return plistlib.load(f)

def get_playlists():
    """
    Get list of all playlists in the library.

    Returns:
        list of dict: Each dict contains 'Name', 'Playlist ID', and 'Track Count'
    """
    library_data = load_raw_library()
    playlists = library_data.get("Playlists", [])

    result = []
    for playlist in playlists:
        result.append({
            "Name": playlist.get("Name", "Unknown"),
            "Playlist ID": playlist.get("Playlist Persistent ID", ""),
            "Track Count": len(playlist.get("Playlist Items", []))
        })
    return result

def get_playlist_track_ids(playlist_name):
    """
    Get set of Track IDs for a specific playlist.

    Args:
        playlist_name (str): Name of the playlist (case-sensitive)

    Returns:
        set: Set of Track IDs (as strings) in the playlist

    Raises:
        ValueError: If playlist not found
    """
    library_data = load_raw_library()
    playlists = library_data.get("Playlists", [])

    for playlist in playlists:
        if playlist.get("Name") == playlist_name:
            items = playlist.get("Playlist Items", [])
            return {str(item["Track ID"]) for item in items}

    raise ValueError(f"Playlist '{playlist_name}' not found")

def load_playlist(playlist_name):
    """
    Load tracks from a specific playlist.

    Args:
        playlist_name (str): Name of the playlist

    Returns:
        pd.DataFrame: DataFrame containing only tracks from the playlist
    """
    track_ids = get_playlist_track_ids(playlist_name)
    df = load_library()
    return df[df["Track ID"].isin(track_ids)]

def load_dj_playlists():
    """
    Load tracks from both DJ master playlists (MASTER LIST DJ AUDIO and MASTER LIST DJ VIDEO).

    Returns:
        pd.DataFrame: DataFrame containing tracks from both DJ playlists (no duplicates)
    """
    try:
        audio_ids = get_playlist_track_ids("MASTER LIST DJ AUDIO")
    except ValueError:
        audio_ids = set()

    try:
        video_ids = get_playlist_track_ids("MASTER LIST DJ VIDEO")
    except ValueError:
        video_ids = set()

    dj_track_ids = audio_ids | video_ids  # Union of both sets
    df = load_library()
    return df[df["Track ID"].isin(dj_track_ids)]

def filter_library_to_playlists(df, playlist_names):
    """
    Filter a library DataFrame to only include tracks from specified playlists.

    Args:
        df (pd.DataFrame): Library DataFrame from load_library()
        playlist_names (list of str): List of playlist names to include

    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    all_track_ids = set()
    for playlist_name in playlist_names:
        try:
            track_ids = get_playlist_track_ids(playlist_name)
            all_track_ids |= track_ids
        except ValueError:
            print(f"Warning: Playlist '{playlist_name}' not found, skipping")

    return df[df["Track ID"].isin(all_track_ids)]

def load_library():
    path = os.path.expanduser(XML_LIBRARY_PATH)
    with open(path, 'rb') as f:
        library_data = plistlib.load(f)
    tracks_dict = library_data["Tracks"]
    rows = []
    for track_id, track_info in tracks_dict.items():
        row = {
            "Track ID": track_id,
            "Name": track_info.get("Name", ""),
            "Artist": track_info.get("Artist", ""),
            "Album": track_info.get("Album", ""),
            "Album Artist": track_info.get("Album Artist", ""),
            "Genre": track_info.get("Genre", ""),
            "Grouping": track_info.get("Grouping", ""),
            "Comments": track_info.get("Comments", ""),
            "Year": track_info.get("Year", ""),         # blank if missing
            "Rating": track_info.get("Rating", 0),        # default 0 if missing
            "Play Count": track_info.get("Play Count", 0),
            "Skip Count": track_info.get("Skip Count", 0),
            "Bit Rate": track_info.get("Bit Rate", 0),
            "Sample Rate": track_info.get("Sample Rate", 0),  # still read but not displayed
            "Size": track_info.get("Size", 0),
            "Kind": track_info.get("Kind", ""),
            "Cloud Status": track_info.get("Cloud Status", ""),
            "BPM": track_info.get("BPM", 0),
            "Favorite": track_info.get("Loved", False),
            "Compilation": track_info.get("Compilation", False),
            "Date Added": track_info.get("Date Added", None),
            "Last Played": track_info.get("Play Date UTC", None),
            "Last Skipped": track_info.get("Skip Date", None),
            "Checked": not track_info.get("Disabled", False),
            "Duration (ms)": track_info.get("Total Time", 0),
            "Track Type": track_info.get("Track Type", ""),
            "File Type": track_info.get("File Type", ""),
            "Has Video": track_info.get("Has Video", False),
            "Protected": track_info.get("Protected", False)
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    return df

def add_tracks_to_playlist(track_ids, playlist_name):
    """Add tracks to an Apple Music playlist by database ID.

    Creates the playlist if it doesn't exist.

    Args:
        track_ids (list): List of database IDs (int or str)
        playlist_name (str): Target playlist name

    Returns:
        tuple: (success_count, error_count)
    """
    escaped_name = playlist_name.replace('"', '\\"')
    id_list = ', '.join(str(tid) for tid in track_ids)
    script = f'''
    tell application "Music"
        try
            set targetPlaylist to user playlist "{escaped_name}"
        on error
            set targetPlaylist to (make new user playlist with properties {{name:"{escaped_name}"}})
        end try
        set successCount to 0
        set errorCount to 0
        repeat with trackID in {{{id_list}}}
            try
                set aTrack to (first track of library playlist 1 whose database ID is trackID)
                duplicate aTrack to targetPlaylist
                set successCount to successCount + 1
            on error
                set errorCount to errorCount + 1
            end try
        end repeat
        return (successCount as text) & "," & (errorCount as text)
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, check=True
        )
        parts = result.stdout.strip().split(',')
        return int(parts[0]), int(parts[1])
    except subprocess.CalledProcessError as e:
        print(f"Error adding tracks to playlist: {e.stderr}")
        return 0, len(track_ids)


def remove_accents(text):
    """Remove accented characters from a given string."""
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def normalize_title(title):
    """
    Normalize the title by first removing accents and then stripping out common suffixes
    such as (Video), (Remix), (Extended), etc.
    """
    # Remove accented characters so that, e.g., "vidéo" becomes "video".
    title_no_accents = remove_accents(title)
    # Remove common suffixes using regex.
    normalized = re.sub(r'\s*\(.*?(video|remix|extended).*?\)', '', title_no_accents, flags=re.IGNORECASE)
    return normalized.strip()

def main():
    df = load_library()
    
    # Create a normalized title column.
    df['Normalized Title'] = df['Name'].apply(normalize_title)
    
    # Compute a grouping artist: use "Album Artist" if populated, else fallback to "Artist".
    # Remove accents for consistent grouping.
    df['Grouping Artist'] = df.apply(
        lambda row: remove_accents(row['Album Artist']) if row['Album Artist'].strip() != "" else remove_accents(row['Artist']),
        axis=1
    )
    
    # Convert "Date Added" to datetime for proper sorting.
    df['Date Added'] = pd.to_datetime(df['Date Added'], errors='coerce')
    
    # Group by "Grouping Artist" and normalized title.
    grouped = df.groupby(['Grouping Artist', 'Normalized Title'])
    
    discrepancies = []
    
    # Iterate through groups and check for discrepancies in Year, Genre, or Rating.
    for (group_artist, norm_title), group in grouped:
        unique_years = group['Year'].unique()
        unique_genres = group['Genre'].unique()
        unique_ratings = group['Rating'].unique()
        
        if len(unique_years) > 1 or len(unique_genres) > 1: # or len(unique_ratings) > 1:
            # Determine the most recent Date Added in the group.
            most_recent_date = group['Date Added'].max()
            discrepancies.append({
                'Grouping Artist': group_artist,
                'Normalized Title': norm_title,
                'Group Data': group,
                'Most Recent Date': most_recent_date
            })
    
    # Order groups by the most recent Date Added (descending).
    discrepancies = sorted(discrepancies, key=lambda x: x['Most Recent Date'], reverse=True)

    print(f"\nNumber of groups of songs with discrepancies: {len(discrepancies)}\n")
    
    # Process and display one group at a time.
    for disc in discrepancies:
        print("=" * 40)
        print(f"Grouping Artist: {disc['Grouping Artist']}")
        print(f"Song Group: {disc['Normalized Title']}")
        print(f"Most Recent Date Added: {disc['Most Recent Date']}")
        print("-" * 40)
        # Display relevant columns: the original Artist field is included for featured artist inspection.
        display_columns = ['Name', 'Track ID', 'Artist', 'Year', 'Genre', 'Rating', 'Date Added', 'Kind', 'Bit Rate', 'Size']
        print(disc['Group Data'][display_columns].to_string(index=False))
        print("=" * 40)
        input("Press Enter to view the next group...")

if __name__ == "__main__":
    main()



