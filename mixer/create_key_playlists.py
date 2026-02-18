#!/usr/bin/env python3
"""
create_key_playlists.py

Creates 22 smart playlists in Apple Music by duplicating an existing template
smart playlist and renaming each copy to match the correct effective-key pattern.

Already existing (skipped): "6A or 1A(-1) or 11A(+1)"  and  "12A or 5A(+1) or 7A(-1)"

Run once from the project root:
    python3 mixer/create_key_playlists.py

After running, open each new playlist in Apple Music and update the three
Comment-begins-with conditions to match the keys in its name.
"""

import subprocess
import sys
import time

# Template to duplicate — must already exist as a smart playlist in Apple Music.
TEMPLATE = "12A or 5A(+1) or 7A(-1)"

# All 24 correct names (computed from camelot_to_pitch in camelot.py).
# 6A and 12A already exist, so they are skipped below.
ALL_24 = [
    "1A or 6A(+1) or 8A(-1)",
    "2A or 7A(+1) or 9A(-1)",
    "3A or 8A(+1) or 10A(-1)",
    "4A or 9A(+1) or 11A(-1)",
    "5A or 10A(+1) or 12A(-1)",
    "6A or 11A(+1) or 1A(-1)",   # already exists (skipped)
    "7A or 12A(+1) or 2A(-1)",
    "8A or 1A(+1) or 3A(-1)",
    "9A or 2A(+1) or 4A(-1)",
    "10A or 3A(+1) or 5A(-1)",
    "11A or 4A(+1) or 6A(-1)",
    "12A or 5A(+1) or 7A(-1)",   # already exists (skipped)
    "1B or 6B(+1) or 8B(-1)",
    "2B or 7B(+1) or 9B(-1)",
    "3B or 8B(+1) or 10B(-1)",
    "4B or 9B(+1) or 11B(-1)",
    "5B or 10B(+1) or 12B(-1)",
    "6B or 11B(+1) or 1B(-1)",
    "7B or 12B(+1) or 2B(-1)",
    "8B or 1B(+1) or 3B(-1)",
    "9B or 2B(+1) or 4B(-1)",
    "10B or 3B(+1) or 5B(-1)",
    "11B or 4B(+1) or 6B(-1)",
    "12B or 5B(+1) or 7B(-1)",
]

# Names that already exist and should not be recreated.
ALREADY_EXIST = {
    "6A or 1A(-1) or 11A(+1)",   # user's existing 6A playlist (alternative ordering, same conditions)
    "6A or 11A(+1) or 1A(-1)",   # canonical ordering
    "12A or 5A(+1) or 7A(-1)",
}

TO_CREATE = [n for n in ALL_24 if n not in ALREADY_EXIST]


def run_applescript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def duplicate_and_rename(new_name: str) -> None:
    # Escape any double-quotes in the name just in case (none expected here).
    safe_name = new_name.replace('"', '\\"')
    script = f'''
tell application "Music"
    set srcPL to first playlist whose name is "{TEMPLATE}"
    set newPL to (duplicate srcPL)
    set name of newPL to "{safe_name}"
end tell
'''
    run_applescript(script)


def main() -> None:
    print(f'Template : "{TEMPLATE}"')
    print(f"Creating : {len(TO_CREATE)} playlists  (skipping {len(ALL_24) - len(TO_CREATE)} that already exist)\n")

    errors: list[str] = []
    for i, name in enumerate(TO_CREATE, 1):
        try:
            duplicate_and_rename(name)
            print(f"  [{i:2d}/{len(TO_CREATE)}] ✓  {name}")
        except RuntimeError as exc:
            print(f"  [{i:2d}/{len(TO_CREATE)}] ✗  {name}  —  {exc}", file=sys.stderr)
            errors.append(name)
        time.sleep(0.3)  # brief pause between AppleScript calls

    print()
    if errors:
        print(f"Errors ({len(errors)}):")
        for n in errors:
            print(f"  - {n}")
        sys.exit(1)
    else:
        print(
            "Done. All playlists created.\n"
            "Next: open each new playlist in Apple Music and update the three\n"
            "Comment-begins-with conditions to match the keys shown in its name."
        )


if __name__ == "__main__":
    main()
