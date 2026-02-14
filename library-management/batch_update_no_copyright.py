#!/usr/bin/env python3
"""
Batch Update: Set Year to 2022 for all "No Copyright Music" tracks

Updates all tracks by artist "No Copyright Music" that are missing year metadata.
Sets year to 2022 (when they were added to library).
"""
import subprocess
import time
import json
from datetime import datetime


def run_applescript(script):
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


print("="*70)
print("BATCH UPDATE: No Copyright Music Tracks - Year 2022")
print("="*70)

# Step 1: Find all "No Copyright Music" tracks with missing year
print("\n[1/5] Searching for 'No Copyright Music' tracks with missing year...")

search_script = '''
tell application "Music"
    set searchResults to (search library playlist 1 for "No Copyright Music")

    set trackList to {}
    repeat with aTrack in searchResults
        if (artist of aTrack is "No Copyright Music") then
            try
                set trackYear to year of aTrack
            on error
                set trackYear to 0
            end try

            -- Only include tracks with missing year
            if trackYear is 0 then
                set trackID to database ID of aTrack
                set trackName to name of aTrack
                set trackArtist to artist of aTrack

                try
                    set trackGenre to genre of aTrack
                on error
                    set trackGenre to ""
                end try

                set trackData to (trackID as text) & "|" & trackName & "|" & trackArtist & "|" & (trackYear as text) & "|" & trackGenre
                set end of trackList to trackData
            end if
        end if
    end repeat

    set AppleScript's text item delimiters to linefeed
    return trackList as text
end tell
'''

result = run_applescript(search_script)

tracks = []
for line in result.split('\n'):
    if not line:
        continue
    parts = line.split('|')
    if len(parts) >= 5:
        tracks.append({
            'id': parts[0],
            'name': parts[1],
            'artist': parts[2],
            'year': int(parts[3]) if parts[3] != '0' else None,
            'genre': parts[4] if parts[4] else '(empty)'
        })

print(f"✓ Found {len(tracks)} tracks missing year")

if len(tracks) == 0:
    print("\n✓ All 'No Copyright Music' tracks already have year set!")
    exit(0)

# Step 2: Show summary
print(f"\n{'='*70}")
print("TRACKS TO UPDATE:")
print(f"{'='*70}")

print(f"\nFirst 10 tracks:")
for i, track in enumerate(tracks[:10], 1):
    print(f"  {i}. {track['name'][:60]}")
    print(f"     Genre: {track['genre']}, Year: (empty) → 2022")

if len(tracks) > 10:
    print(f"\n  ... and {len(tracks) - 10} more tracks")

# Step 3: Confirm
print(f"\n{'='*70}")
print("CONFIRMATION:")
print(f"{'='*70}")
print(f"Will update {len(tracks)} tracks:")
print(f"  Artist: No Copyright Music")
print(f"  Year: (empty) → 2022")

response = input(f"\nProceed with updating {len(tracks)} tracks? (yes/no): ")
if response.lower() != 'yes':
    print("Cancelled.")
    exit(0)

# Step 4: Batch update
print(f"\n[2/5] Updating tracks...")
print(f"{'='*70}")

successful = 0
failed = 0
update_log = []
start_time = time.time()

for i, track in enumerate(tracks, 1):
    track_id = track['id']
    track_name = track['name']

    # Show progress every 5 tracks
    if i % 5 == 0 or i == 1 or i == len(tracks):
        elapsed = time.time() - start_time
        rate = i / elapsed if elapsed > 0 else 0
        remaining = (len(tracks) - i) / rate if rate > 0 else 0
        print(f"\nProgress: {i}/{len(tracks)} ({i/len(tracks)*100:.1f}%) - {elapsed:.1f}s elapsed, ~{remaining:.1f}s remaining")

    print(f"  {i}. Updating {track_name[:50]}...")

    # Update year
    update_script = f'''
    tell application "Music"
        try
            set targetTrack to (first track of library playlist 1 whose database ID is {track_id})
            set year of targetTrack to 2022
            return "success"
        on error errMsg
            return "error: " & errMsg
        end try
    end tell
    '''

    try:
        result = run_applescript(update_script)
        if result == "success":
            print(f"     ✓ Success")
            successful += 1
            update_log.append({
                'track_id': track_id,
                'name': track_name,
                'status': 'success',
                'old_year': None,
                'new_year': 2022
            })
        else:
            print(f"     ✗ Failed: {result}")
            failed += 1
            update_log.append({
                'track_id': track_id,
                'name': track_name,
                'status': 'failed',
                'error': result
            })
    except Exception as e:
        print(f"     ✗ Error: {e}")
        failed += 1
        update_log.append({
            'track_id': track_id,
            'name': track_name,
            'status': 'error',
            'error': str(e)
        })

    # Small delay to avoid overwhelming Music app
    time.sleep(0.1)

total_time = time.time() - start_time

# Step 5: Verify a sample
print(f"\n[3/5] Verifying sample tracks...")

# Verify first, middle, and last track
sample_indices = [0, len(tracks) // 2, len(tracks) - 1] if len(tracks) > 2 else [0]
verified_count = 0

for idx in sample_indices:
    track = tracks[idx]
    verify_script = f'''
    tell application "Music"
        set targetTrack to (first track of library playlist 1 whose database ID is {track['id']})
        return year of targetTrack as text
    end tell
    '''

    try:
        result = run_applescript(verify_script)
        verified_year = int(result) if result != '0' else None

        if verified_year == 2022:
            print(f"  ✓ Track {idx + 1}: Year = 2022")
            verified_count += 1
        else:
            print(f"  ✗ Track {idx + 1}: Year = {verified_year} (expected 2022)")
    except Exception as e:
        print(f"  ✗ Track {idx + 1}: Verification error: {e}")

# Step 6: Save log
print(f"\n[4/5] Saving update log...")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = f"batch_update_log_{timestamp}.json"

log_data = {
    'timestamp': timestamp,
    'artist': 'No Copyright Music',
    'field': 'year',
    'new_value': 2022,
    'total_tracks': len(tracks),
    'successful': successful,
    'failed': failed,
    'duration_seconds': total_time,
    'tracks': update_log
}

with open(log_file, 'w') as f:
    json.dump(log_data, f, indent=2)

print(f"✓ Log saved: {log_file}")

# Step 7: Summary
print(f"\n[5/5] Update Complete!")
print(f"{'='*70}")
print("SUMMARY:")
print(f"{'='*70}")
print(f"Total tracks: {len(tracks)}")
print(f"Successful: {successful} ({successful/len(tracks)*100:.1f}%)")
print(f"Failed: {failed} ({failed/len(tracks)*100:.1f}%)")
print(f"Verified: {verified_count}/{len(sample_indices)} samples")
print(f"Duration: {total_time:.1f} seconds ({total_time/len(tracks):.2f}s per track)")

if successful == len(tracks):
    print(f"\n✅ ALL TRACKS UPDATED SUCCESSFULLY!")
    print(f"\n⚠️  Recommendation: Re-export your library XML to update the cache")
elif failed > 0:
    print(f"\n⚠️  {failed} tracks failed to update - see log file for details")

print("="*70)
