#!/usr/bin/env python3
"""
Test: Update genre for Hymn by Barclay James Harvest

Updates the Hymn track missing genre to "Rock, Classic Rock"
User should watch the Apple Music info window to see the change happen.
"""
import subprocess
import time


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
print("TEST: Update Genre for Hymn by Barclay James Harvest")
print("="*70)

# We know from previous test: Database ID 61754 is missing genre
track_id = 61754
new_genre = "Rock, Classic Rock"

print(f"\nTarget Track:")
print(f"  Database ID: {track_id}")
print(f"  Name: Hymn")
print(f"  Artist: Barclay James Harvest")

# Step 1: Read current state
print(f"\n[1/4] Reading current state from Music...")

read_script = f'''
tell application "Music"
    set targetTrack to (first track of library playlist 1 whose database ID is {track_id})

    set trackName to name of targetTrack
    set trackArtist to artist of targetTrack
    set trackYear to year of targetTrack

    try
        set trackGenre to genre of targetTrack
    on error
        set trackGenre to ""
    end try

    return trackName & "|" & trackArtist & "|" & (trackYear as text) & "|" & trackGenre
end tell
'''

result = run_applescript(read_script)
parts = result.split('|')

current_name = parts[0]
current_artist = parts[1]
current_year = parts[2]
current_genre = parts[3] if parts[3] else "(empty)"

print(f"✓ Current state:")
print(f"  Name: {current_name}")
print(f"  Artist: {current_artist}")
print(f"  Year: {current_year}")
print(f"  Genre: {current_genre}")

# Step 2: Confirm update
print(f"\n{'='*70}")
print("PROPOSED UPDATE:")
print(f"{'='*70}")
print(f"Will set Genre to: {new_genre}")
print(f"\n⚠️  WATCH the Apple Music info window - you should see the genre field populate!")

response = input("\nProceed with update? (yes/no): ")
if response.lower() != 'yes':
    print("Cancelled.")
    exit(0)

# Step 3: Update genre
print(f"\n[2/4] Setting genre to '{new_genre}'...")

update_script = f'''
tell application "Music"
    set targetTrack to (first track of library playlist 1 whose database ID is {track_id})
    set genre of targetTrack to "{new_genre}"
    return "success"
end tell
'''

try:
    result = run_applescript(update_script)
    print(f"✓ AppleScript completed")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Step 4: Wait for Music to update
print("\n[3/4] Waiting 1 second for Music to update...")
time.sleep(1)

# Step 5: Verify the change
print("\n[4/4] Verifying change in Music...")

verify_script = f'''
tell application "Music"
    set targetTrack to (first track of library playlist 1 whose database ID is {track_id})

    try
        set trackGenre to genre of targetTrack
    on error
        set trackGenre to ""
    end try

    return trackGenre
end tell
'''

result = run_applescript(verify_script)
verified_genre = result if result else "(empty)"

print(f"✓ Verified from Music:")
print(f"  Genre: {verified_genre}")

# Step 6: Check success
print(f"\n{'='*70}")
if verified_genre == new_genre:
    print("✅ SUCCESS! Genre updated to 'Rock, Classic Rock'")
    print("\n⚠️  Check the Apple Music info window - do you see the genre field now?")
else:
    print(f"✗ FAILED - Genre is '{verified_genre}', expected '{new_genre}'")

print("="*70)
