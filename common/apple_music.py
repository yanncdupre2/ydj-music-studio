import os
import re
import plistlib
import pandas as pd
import unicodedata

XML_LIBRARY_PATH = "~/YDJ Library.xml"

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



