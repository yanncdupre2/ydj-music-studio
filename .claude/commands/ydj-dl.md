Download every new song from the "ydj dl" YouTube playlist, then dry-run the rename.

## Workflow

You are working in the `ydj-music-studio` project. Downloads use the global yt-dlp
config at `~/.config/yt-dlp/config` (h264 ≤1080p, Safari cookies, saves to
`~/Movies/YouTube Downloads/`).

- **Playlist:** `https://www.youtube.com/playlist?list=PL_S6BfDZ5FTYSBd1-eE1ZAY6ISaevy30R`
- **Download archive:** `~/.config/yt-dlp/ydj-dl-archive.txt` — one line per video
  yt-dlp has fully downloaded. It lets re-runs skip songs already fetched (renaming
  defeats `--no-overwrites`), and it is the gate `/ydj-dl-empty` uses to decide what
  is safe to remove from the playlist. Never edit or delete it by hand.

### Step 1: Download (ONE command, run in the background)
```bash
yt-dlp --download-archive ~/.config/yt-dlp/ydj-dl-archive.txt \
  "https://www.youtube.com/playlist?list=PL_S6BfDZ5FTYSBd1-eE1ZAY6ISaevy30R"
```
Run it with `run_in_background` and wait for it to exit; do not poll. Do not pass
`--ignore-errors` / `--abort-on-error` overrides — the config's defaults apply.

If it fails with `The playlist does not exist`, the Safari session is not signed in
to the YouTube account that owns the playlist. Stop and tell the user to open the
playlist URL in Safari while signed in, then re-run.

### Step 2: Report
From the output, report to the user:
- How many entries the playlist had, how many were downloaded this run, and how many
  were skipped as already in the archive
- Every entry that **failed** (unavailable, private, age-gated, format error), by
  title — these are NOT in the archive and `/ydj-dl-empty` will leave them in the
  playlist

### Step 3: Rename dry-run
```bash
cd /Users/fydupre/Projects/ydj-music-studio && python3 downloads/rename_youtube.py
```
Show the proposed renames. Only run `python3 downloads/rename_youtube.py --apply`
after the user approves them.
