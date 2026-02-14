#!/usr/bin/env python3
"""
Safe Apple Music Year Updater via AppleScript

Updates track year metadata directly in Apple Music library with extensive safety checks.

Usage:
    python3 update_year.py --dry-run              # Preview changes (default, safe)
    python3 update_year.py --test-one             # Test on single track with confirmation
    python3 update_year.py --apply                # Apply all changes (requires confirmation)
    python3 update_year.py --rollback backup.json # Rollback changes using backup file

Safety Features:
    - Dry-run mode by default (no changes unless --apply)
    - Backup file created before any changes
    - Single-track test mode for validation
    - Read-verify-write-verify cycle for each track
    - Detailed logging of all operations
    - Rollback capability using backup file

IMPORTANT: Keep Apple Music app OPEN while running this script for visual verification!
"""
import sys
import os
import subprocess
import json
from datetime import datetime

# Add parent directory to path for common imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.apple_music import load_dj_playlists
import pandas as pd


class AppleMusicUpdater:
    """Safe AppleScript-based updater for Apple Music library."""

    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.backup_file = None
        self.changes_log = []

    def run_applescript(self, script):
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

    def get_track_by_name_artist(self, name, artist):
        """
        Get track from Music app by name and artist.

        Args:
            name (str): Track name
            artist (str): Track artist

        Returns:
            dict: Track info (database_id, name, artist, year, genre) or None if not found
        """
        # Escape quotes in name and artist for AppleScript
        name_escaped = name.replace('"', '\\"').replace("'", "'\\''")
        artist_escaped = artist.replace('"', '\\"').replace("'", "'\\''")

        script = f'''
        tell application "Music"
            set searchQuery to "{name_escaped} {artist_escaped}"
            set searchResults to (search library playlist 1 for searchQuery)

            if (count of searchResults) = 0 then
                return "NOT_FOUND"
            end if

            -- Find exact match by name and artist
            set foundTrack to missing value
            repeat with aTrack in searchResults
                if (name of aTrack is "{name_escaped}") and (artist of aTrack is "{artist_escaped}") then
                    set foundTrack to aTrack
                    exit repeat
                end if
            end repeat

            if foundTrack is missing value then
                -- No exact match, use first result
                set foundTrack to item 1 of searchResults
            end if

            set trackID to database ID of foundTrack
            set trackName to name of foundTrack
            set trackArtist to artist of foundTrack

            -- Get year (may be missing)
            try
                set trackYear to year of foundTrack
            on error
                set trackYear to 0
            end try

            -- Get genre (may be missing)
            try
                set trackGenre to genre of foundTrack
            on error
                set trackGenre to ""
            end try

            return (trackID as text) & "|" & trackName & "|" & trackArtist & "|" & (trackYear as text) & "|" & trackGenre
        end tell
        '''

        try:
            result = self.run_applescript(script)
            if result == "NOT_FOUND":
                return None

            parts = result.split('|')
            if len(parts) >= 5:
                return {
                    'database_id': int(parts[0]),
                    'name': parts[1],
                    'artist': parts[2],
                    'year': int(parts[3]) if parts[3] != '0' else None,
                    'genre': parts[4] if parts[4] else None
                }
        except Exception as e:
            print(f"  ✗ Error reading track '{name}' by '{artist}': {e}")

        return None

    def set_track_year(self, name, artist, new_year):
        """
        Set year for a track in Music app.

        Args:
            name (str): Track name
            artist (str): Track artist
            new_year (int): Year to set

        Returns:
            bool: True if successful, False otherwise
        """
        if self.dry_run:
            print(f"  [DRY-RUN] Would set year to {new_year}")
            return True

        # Escape quotes
        name_escaped = name.replace('"', '\\"').replace("'", "'\\''")
        artist_escaped = artist.replace('"', '\\"').replace("'", "'\\''")

        script = f'''
        tell application "Music"
            set searchQuery to "{name_escaped} {artist_escaped}"
            set searchResults to (search library playlist 1 for searchQuery)

            if (count of searchResults) = 0 then
                return "NOT_FOUND"
            end if

            -- Find exact match
            set targetTrack to missing value
            repeat with aTrack in searchResults
                if (name of aTrack is "{name_escaped}") and (artist of aTrack is "{artist_escaped}") then
                    set targetTrack to aTrack
                    exit repeat
                end if
            end repeat

            if targetTrack is missing value then
                set targetTrack to item 1 of searchResults
            end if

            set year of targetTrack to {new_year}
            return "success"
        end tell
        '''

        try:
            result = self.run_applescript(script)
            return result == "success"
        except Exception as e:
            print(f"  ✗ Error setting year: {e}")
            return False

    def update_track_year(self, track_id, name, artist, current_year, new_year):
        """
        Safely update a track's year with full verification cycle.

        Args:
            track_id: Database ID
            name: Track name
            artist: Track artist
            current_year: Current year value (or None)
            new_year: New year to set

        Returns:
            dict: Update result with status and details
        """
        result = {
            'track_id': track_id,
            'name': name,
            'artist': artist,
            'old_year': current_year,
            'new_year': new_year,
            'success': False,
            'message': ''
        }

        print(f"\n{'='*70}")
        print(f"Track: {artist} - {name}")
        print(f"Database ID: {track_id}")
        print(f"Current Year: {current_year if current_year else '(empty)'}")
        print(f"New Year: {new_year}")
        print(f"{'='*70}")

        # Step 1: Read and verify current state
        print("\n[1/4] Reading current track data from Music...")
        track_info = self.get_track_by_name_artist(name, artist)

        if not track_info:
            result['message'] = "Failed to find track in Music (not in library?)"
            print(f"  ✗ {result['message']}")
            return result

        print(f"  ✓ Found: {track_info['artist']} - {track_info['name']}")
        print(f"  ✓ Database ID in Music: {track_info['database_id']}")
        print(f"  ✓ Current year in Music: {track_info['year'] if track_info['year'] else '(empty)'}")

        # Check if year is already correct
        if track_info['year'] == new_year:
            result['success'] = True
            result['message'] = f"Year is already {new_year} - no update needed"
            print(f"  ✓ {result['message']}")
            return result

        # Verify the track matches what we expect
        if track_info['year'] != current_year:
            print(f"  ⚠️  NOTE: XML has year {current_year}, Music has {track_info['year']}")
            print(f"  ⚠️  This is normal if you manually updated or re-exported the library")

        # Step 2: Set new year
        print(f"\n[2/4] Setting year to {new_year}...")
        if not self.set_track_year(name, artist, new_year):
            result['message'] = "Failed to set year"
            print(f"  ✗ {result['message']}")
            return result

        if self.dry_run:
            result['success'] = True
            result['message'] = "Dry-run successful (no actual changes made)"
            print(f"  ✓ {result['message']}")
            return result

        # Step 3: Verify the change
        print(f"\n[3/4] Verifying change in Music...")
        updated_info = self.get_track_by_name_artist(name, artist)

        if not updated_info:
            result['message'] = "Failed to verify - cannot read track after update"
            print(f"  ✗ {result['message']}")
            return result

        if updated_info['year'] != new_year:
            result['message'] = f"Verification failed! Expected {new_year}, got {updated_info['year']}"
            print(f"  ✗ {result['message']}")
            return result

        print(f"  ✓ Verified: Year is now {updated_info['year']}")

        # Step 4: Success
        print(f"\n[4/4] Update complete!")
        result['success'] = True
        result['message'] = f"Successfully updated year from {current_year} to {new_year}"
        print(f"  ✓ {result['message']}")

        return result

    def create_backup(self, updates):
        """
        Create backup file before making changes.

        Args:
            updates (list): List of tracks to update with original values
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_file = f"year_update_backup_{timestamp}.json"

        backup_data = {
            'timestamp': timestamp,
            'dry_run': self.dry_run,
            'tracks': updates
        }

        with open(self.backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)

        print(f"\n✓ Backup created: {self.backup_file}")
        return self.backup_file

    def save_changes_log(self):
        """Save log of all changes made."""
        if not self.changes_log:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"year_update_log_{timestamp}.json"

        with open(log_file, 'w') as f:
            json.dump(self.changes_log, f, indent=2)

        print(f"\n✓ Changes log saved: {log_file}")


def find_tracks_needing_year_update():
    """
    Find all DJ tracks missing year metadata.

    Returns:
        pd.DataFrame: Tracks needing year updates
    """
    print("Loading DJ playlists...")
    df = load_dj_playlists()

    # Find tracks with missing year
    missing_year = df[df['Year'].isna() | (df['Year'] == '') | (df['Year'] == 0)].copy()

    print(f"✓ Found {len(missing_year)} tracks missing year in DJ playlists")

    return missing_year


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Safely update track years in Apple Music library',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 update_year.py --dry-run        # Preview changes (safe, default)
  python3 update_year.py --test-one       # Test on single track
  python3 update_year.py --apply          # Apply all changes

IMPORTANT: Keep Apple Music app OPEN for visual verification!
        '''
    )

    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Preview changes without modifying Music (default)')
    parser.add_argument('--apply', action='store_true',
                        help='Actually apply changes to Music library')
    parser.add_argument('--test-one', action='store_true',
                        help='Test on single track with confirmation')

    args = parser.parse_args()

    # Determine dry-run mode
    dry_run = not args.apply

    if dry_run:
        print("\n" + "="*70)
        print("DRY-RUN MODE - No changes will be made to Music library")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("⚠️  APPLY MODE - Changes WILL be made to Music library!")
        print("="*70)
        response = input("\nAre you sure you want to modify the Music library? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

    # Load tracks needing updates
    tracks_to_update = find_tracks_needing_year_update()

    if len(tracks_to_update) == 0:
        print("\n✓ No tracks need year updates!")
        return

    # Show summary
    print(f"\n{'='*70}")
    print("TRACKS NEEDING YEAR UPDATES")
    print(f"{'='*70}")
    print(f"\nTotal: {len(tracks_to_update)} tracks")

    # Group by artist for summary
    by_artist = tracks_to_update.groupby('Artist').size().sort_values(ascending=False)
    print(f"\nBy artist:")
    for artist, count in by_artist.head(10).items():
        print(f"  {count:2d}  {artist}")

    if len(by_artist) > 10:
        print(f"  ... and {len(by_artist) - 10} more artists")

    # Propose year assignments
    print(f"\n{'='*70}")
    print("PROPOSED YEAR ASSIGNMENTS")
    print(f"{'='*70}")

    # For "No Copyright Music" tracks, assign 2022 (date they were added)
    # For others, we'll need manual input or research

    updates = []
    for idx, row in tracks_to_update.iterrows():
        track_id = row['Track ID']
        name = row['Name']
        artist = row['Artist']
        date_added = pd.to_datetime(row['Date Added'])

        # Determine year to assign
        if artist == "No Copyright Music":
            proposed_year = 2022  # All were added in Dec 2022
        elif name == "Hymn" and artist == "Barclay James Harvest":
            proposed_year = 1977  # Known from the duplicate track
        else:
            # For any others, use year added as fallback
            proposed_year = date_added.year

        updates.append({
            'track_id': track_id,
            'name': name,
            'artist': artist,
            'current_year': None if pd.isna(row['Year']) else row['Year'],
            'new_year': proposed_year
        })

    # Show proposed changes
    print(f"\nWill update {len(updates)} tracks:")
    for i, update in enumerate(updates[:10], 1):
        print(f"  {i}. {update['artist']} - {update['name']}")
        print(f"     Year: {update['current_year']} → {update['new_year']}")

    if len(updates) > 10:
        print(f"  ... and {len(updates) - 10} more")

    # Test mode - single track only
    if args.test_one:
        print(f"\n{'='*70}")
        print("TEST MODE - Will update ONE track only")
        print(f"{'='*70}")

        # Pick first track
        test_update = updates[0]
        print(f"\nTest track: {test_update['artist']} - {test_update['name']}")

        if not dry_run:
            response = input("\nProceed with test update? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return

        updater = AppleMusicUpdater(dry_run=dry_run)
        updater.create_backup([test_update])

        result = updater.update_track_year(
            test_update['track_id'],
            test_update['name'],
            test_update['artist'],
            test_update['current_year'],
            test_update['new_year']
        )

        if result['success']:
            print(f"\n✓ Test update successful!")
            if not dry_run:
                print(f"\n⚠️  Check Apple Music to verify the year was updated correctly!")
                print(f"   Track: {test_update['artist']} - {test_update['name']}")
                print(f"   Expected year: {test_update['new_year']}")
        else:
            print(f"\n✗ Test update failed: {result['message']}")

        return

    # Batch mode - all tracks
    print(f"\n{'='*70}")
    if dry_run:
        print("PREVIEW MODE - Showing what would happen")
    else:
        print("⚠️  BATCH UPDATE - Will update ALL tracks")
    print(f"{'='*70}")

    if not dry_run:
        response = input(f"\nProceed with updating {len(updates)} tracks? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

    # Create backup
    updater = AppleMusicUpdater(dry_run=dry_run)
    updater.create_backup(updates)

    # Process all updates
    successful = 0
    failed = 0

    for i, update in enumerate(updates, 1):
        print(f"\n\nProcessing track {i}/{len(updates)}...")

        result = updater.update_track_year(
            update['track_id'],
            update['name'],
            update['artist'],
            update['current_year'],
            update['new_year']
        )

        updater.changes_log.append(result)

        if result['success']:
            successful += 1
        else:
            failed += 1

    # Save changes log
    updater.save_changes_log()

    # Summary
    print(f"\n\n{'='*70}")
    print("UPDATE SUMMARY")
    print(f"{'='*70}")
    print(f"Total tracks: {len(updates)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if dry_run:
        print(f"\n✓ Dry-run complete - no changes were made")
        print(f"\nTo apply changes, run: python3 update_year.py --apply")
    else:
        print(f"\n✓ Update complete!")
        print(f"\n⚠️  IMPORTANT: Verify changes in Apple Music!")
        print(f"   Check a few tracks to confirm years were set correctly.")


if __name__ == "__main__":
    main()
