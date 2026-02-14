import pandas as pd
import os
import plistlib
import re

def clean_title(title):
    """
    Clean up the title by removing video-related tags and converting to lowercase.
    """
    if not isinstance(title, str):
        return ""  # Return empty string for null or non-string values
    # Remove anything in parentheses with 'video' (case-insensitive)
    title = re.sub(r'\(.*?video.*?\)', '', title, flags=re.IGNORECASE)
    # Remove excess whitespace and convert to lowercase
    return title.strip().lower()

def clean_artist(artist):
    """
    Clean up the artist name by removing anything after 'ft.', 'feat.', etc., and converting to lowercase.
    """
    if not isinstance(artist, str):
        return ""  # Return empty string for null or non-string values
    # Remove anything after ft., feat., etc.
    artist = re.split(r'\b(ft\.|feat\.|featuring)\b', artist, flags=re.IGNORECASE)[0]
    # Remove excess whitespace and convert to lowercase
    return artist.strip().lower()

def preprocess_music_data(csv_file, output_file):
    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # Ensure required columns exist
    if 'Title' not in df.columns or 'Artist' not in df.columns:
        raise ValueError("The CSV file must contain 'Title' and 'Artist' columns.")

    # Handle null values before applying cleaning functions
    df['Title'] = df['Title'].fillna("")
    df['Artist'] = df['Artist'].fillna("")

    # Add cleaned columns
    df['Cleaned Title'] = df['Title'].apply(clean_title)
    df['Cleaned Artist'] = df['Artist'].apply(clean_artist)

    # Export to a new CSV
    df.to_csv(output_file, index=False)
    print(f"Cleaned data exported to '{output_file}'")

# Main execution
if __name__ == "__main__":

    # Replace with the actual path to your exported Music library XML
    XML_LIBRARY_PATH = "~/YDJ Library.xml"  
    XML_LIBRARY_PATH = os.path.expanduser(XML_LIBRARY_PATH)

    with open(XML_LIBRARY_PATH, 'rb') as f:
        library_data = plistlib.load(f)

    # The 'Tracks' key in the plist contains all track entries
    tracks_dict = library_data["Tracks"]


    all_keys = set()
    for track_info in tracks_dict.values():
        all_keys.update(track_info.keys())

    print("List of all keys found in your iTunes/Apple Music library XML:")
    for key in sorted(all_keys):
        print(key)

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
            "Year": track_info.get("Year", ""),
            "Rating": track_info.get("Rating", 0),                # 0–100?
            "Play Count": track_info.get("Play Count", 0),
            "Skip Count": track_info.get("Skip Count", 0),
            "Checked": not track_info.get("Disabled", False),
            "Duration (ms)": track_info.get("Total Time", 0),  # Duration in ms
            "Bit Rate": track_info.get("Bit Rate", 0),
            "Sample Rate": track_info.get("Sample Rate", 0),
            "Size": track_info.get("Size", 0),                    # file size in bytes
            "Kind": track_info.get("Kind", ""),
            "Cloud Status": track_info.get("Cloud Status", ""),
            "BPM": track_info.get("BPM", 0),
            "Favorited": track_info.get("Favorited", False),           #  → True/False
            "Compilation": track_info.get("Compilation", False),
            "Date Added": track_info.get("Date Added", None),
            "Last Played": track_info.get("Play Date UTC", None),
            "Last Skipped": track_info.get("Skip Date", None),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Quick peek
    print(df.head(10))
    print(df.info())