#!/usr/bin/env python3
"""
Library Cleanup - Discrepancy Detection

Identifies tracks with inconsistent metadata across variants.
Focuses on DJ playlists only (MASTER LIST DJ AUDIO and MASTER LIST DJ VIDEO).

Usage:
    python3 cleanup.py                    # Analyze DJ playlists only
    python3 cleanup.py --all-library      # Analyze entire library
    python3 cleanup.py --playlist "Name"  # Analyze specific playlist
"""
import sys
import os
import argparse

# Add parent directory to path for common imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.apple_music import (
    load_library, load_dj_playlists, load_playlist,
    remove_accents, normalize_title
)
import pandas as pd


def find_discrepancies(df, source_description="library"):
    """
    Find tracks with inconsistent metadata across variants.

    Args:
        df (pd.DataFrame): Library DataFrame
        source_description (str): Description of data source for display

    Returns:
        list: List of discrepancy groups sorted by most recent addition
    """
    # Create normalized title column
    df['Normalized Title'] = df['Name'].apply(normalize_title)

    # Compute grouping artist: use "Album Artist" if populated, else fallback to "Artist"
    df['Grouping Artist'] = df.apply(
        lambda row: remove_accents(row['Album Artist']) if row['Album Artist'].strip() != "" else remove_accents(row['Artist']),
        axis=1
    )

    # Convert "Date Added" to datetime for proper sorting
    df['Date Added'] = pd.to_datetime(df['Date Added'], errors='coerce')

    # Group by "Grouping Artist" and normalized title
    grouped = df.groupby(['Grouping Artist', 'Normalized Title'])

    discrepancies = []

    # Iterate through groups and check for discrepancies in Year, Genre, or Rating
    for (group_artist, norm_title), group in grouped:
        unique_years = group['Year'].unique()
        unique_genres = group['Genre'].unique()
        unique_ratings = group['Rating'].unique()

        if len(unique_years) > 1 or len(unique_genres) > 1:  # or len(unique_ratings) > 1:
            # Determine the most recent Date Added in the group
            most_recent_date = group['Date Added'].max()
            discrepancies.append({
                'Grouping Artist': group_artist,
                'Normalized Title': norm_title,
                'Group Data': group,
                'Most Recent Date': most_recent_date
            })

    # Order groups by the most recent Date Added (descending)
    discrepancies = sorted(discrepancies, key=lambda x: x['Most Recent Date'], reverse=True)

    print(f"\n{'='*60}")
    print(f"Analyzing: {source_description}")
    print(f"Total tracks: {len(df):,}")
    print(f"Groups with discrepancies: {len(discrepancies)}")
    print(f"{'='*60}\n")

    return discrepancies


def display_discrepancies(discrepancies):
    """
    Display discrepancies interactively.

    Args:
        discrepancies (list): List of discrepancy groups
    """
    if not discrepancies:
        print("✓ No discrepancies found! All track variants have consistent metadata.")
        return

    for i, disc in enumerate(discrepancies, 1):
        print("=" * 80)
        print(f"Group {i}/{len(discrepancies)}")
        print(f"Grouping Artist: {disc['Grouping Artist']}")
        print(f"Song Group: {disc['Normalized Title']}")
        print(f"Most Recent Date Added: {disc['Most Recent Date']}")
        print("-" * 80)

        # Display relevant columns
        display_columns = ['Name', 'Track ID', 'Artist', 'Year', 'Genre', 'Rating', 'Date Added', 'Kind', 'Bit Rate', 'Size']
        print(disc['Group Data'][display_columns].to_string(index=False))
        print("=" * 80)

        # Prompt to continue
        if i < len(discrepancies):
            response = input("\nPress Enter to view next group (or 'q' to quit): ")
            if response.lower() == 'q':
                print(f"\nStopped at group {i}/{len(discrepancies)}")
                break
        else:
            print("\n✓ All discrepancies reviewed!")


def main():
    parser = argparse.ArgumentParser(
        description='Find metadata discrepancies in Apple Music library'
    )
    parser.add_argument(
        '--all-library',
        action='store_true',
        help='Analyze entire library instead of just DJ playlists'
    )
    parser.add_argument(
        '--playlist',
        type=str,
        help='Analyze specific playlist by name'
    )

    args = parser.parse_args()

    # Load appropriate data source
    if args.playlist:
        print(f"Loading playlist: {args.playlist}")
        try:
            df = load_playlist(args.playlist)
            source_description = f'Playlist "{args.playlist}"'
        except ValueError as e:
            print(f"Error: {e}")
            return
    elif args.all_library:
        print("Loading entire library...")
        df = load_library()
        source_description = "Entire library"
    else:
        print("Loading DJ playlists (MASTER LIST DJ AUDIO + VIDEO)...")
        df = load_dj_playlists()
        source_description = "DJ Playlists (MASTER LIST DJ AUDIO + VIDEO)"

    # Find and display discrepancies
    discrepancies = find_discrepancies(df, source_description)
    display_discrepancies(discrepancies)


if __name__ == "__main__":
    main()
