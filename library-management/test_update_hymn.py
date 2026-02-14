#!/usr/bin/env python3
"""
Test: Update year for Hymn by Barclay James Harvest

Single track test - updates the Hymn track that's missing genre/year.
User should watch the Apple Music info window to see the change happen.
"""
import subprocess


def run_applescript(script):
    """Execute AppleScript and return result."""
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


print("="*70)
print("TEST: Update Hymn by Barclay James Harvest")
print("="*70)

# Step 1: Find all "Hymn" tracks
print("\n[1/5] Searching for 'Hymn' tracks in Music...")

script = '''
tell application "Music"
    set searchResults to (search library playlist 1 for "Hymn Barclay")

    set trackList to {}
    repeat with aTrack in searchResults
        if (name of aTrack is "Hymn") and (artist of aTrack is "Barclay James Harvest") then
            set trackID to database ID of aTrack
            set trackName to name of aTrack
            set trackArtist to artist of aTrack

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
            set end of trackList to trackData
        end if
    end repeat

    set AppleScript's text item delimiters to linefeed
    return trackList as text
end tell
'''

result = run_applescript(script)
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
            'genre': parts[4] if parts[4] else None
        })

print(f"✓ Found {len(tracks)} 'Hymn' track(s):")
for i, track in enumerate(tracks, 1):
    print(f"\n  {i}. Database ID: {track['id']}")
    print(f"     Year: {track['year'] if track['year'] else '(empty)'}")
    print(f"     Genre: {track['genre'] if track['genre'] else '(empty)'}")

# Find the one missing genre
target_track = None
for track in tracks:
    if not track['genre']:  # Missing genre
        target_track = track
        break

if not target_track:
    print("\n✗ No track found with missing genre")
    print("   Both tracks may already be updated.")
    exit(0)

print(f"\n{'='*70}")
print(f"TARGET TRACK (missing genre):")
print(f"{'='*70}")
print(f"Database ID: {target_track['id']}")
print(f"Name: {target_track['name']}")
print(f"Artist: {target_track['artist']}")
print(f"Current Year: {target_track['year'] if target_track['year'] else '(empty)'}")
print(f"Current Genre: {target_track['genre'] if target_track['genre'] else '(empty)'}")

# Step 2: Confirm update
print(f"\n{'='*70}")
print("PROPOSED UPDATE:")
print(f"{'='*70}")
print(f"Will set Year to: 1977")
print(f"\n⚠️  WATCH the Apple Music info window - you should see the year change!")

response = input("\nProceed with update? (yes/no): ")
if response.lower() != 'yes':
    print("Cancelled.")
    exit(0)

# Step 3: Update year
print(f"\n[2/5] Setting year to 1977...")

update_script = f'''
tell application "Music"
    set targetTrack to (first track of library playlist 1 whose database ID is {target_track['id']})
    set year of targetTrack to 1977
    return "success"
end tell
'''

try:
    result = run_applescript(update_script)
    print(f"✓ AppleScript completed")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Step 4: Wait a moment for Music to update
import time
print("\n[3/5] Waiting 1 second for Music to update...")
time.sleep(1)

# Step 5: Verify the change
print("\n[4/5] Verifying change in Music...")

verify_script = f'''
tell application "Music"
    set targetTrack to (first track of library playlist 1 whose database ID is {target_track['id']})

    set trackID to database ID of targetTrack
    set trackYear to year of targetTrack

    try
        set trackGenre to genre of targetTrack
    on error
        set trackGenre to ""
    end try

    return (trackID as text) & "|" & (trackYear as text) & "|" & trackGenre
end tell
'''

result = run_applescript(verify_script)
parts = result.split('|')

verified_id = parts[0]
verified_year = int(parts[1]) if len(parts) > 1 and parts[1] != '0' else None
verified_genre = parts[2] if len(parts) > 2 and parts[2] else None

print(f"✓ Verified from Music:")
print(f"  Database ID: {verified_id}")
print(f"  Year: {verified_year}")
print(f"  Genre: {verified_genre if verified_genre else '(still empty)'}")

# Step 6: Check success
print(f"\n[5/5] Result:")
if verified_year == 1977:
    print("✅ SUCCESS! Year updated to 1977")
    print("\n⚠️  Check the Apple Music info window - do you see Year: 1977?")
else:
    print(f"✗ FAILED - Year is {verified_year}, expected 1977")

print("\n" + "="*70)
