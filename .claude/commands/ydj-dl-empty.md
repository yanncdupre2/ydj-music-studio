Remove already-downloaded entries from the "ydj dl" YouTube playlist (companion to `/ydj-dl`).

## Workflow

You are working in the `ydj-music-studio` project. The script is
`downloads/ydj_dl_empty.py`. It uses the YouTube Data API v3 and removes **only**
playlist entries whose video ID is in the `/ydj-dl` download archive
(`~/.config/yt-dlp/ydj-dl-archive.txt`). Entries not in the archive are always kept.

Never edit the archive, change the hardcoded playlist ID, or run `--apply` without
the user's explicit go-ahead in this invocation.

### Step 1: Check credentials
If `~/.shared-scripts/ydj-dl-oauth-client.json` does not exist, stop and walk the
user through **First-time setup** below. Do not look for credentials anywhere else.

### Step 2: Dry run (run in the background)
```bash
cd /Users/fydupre/Projects/ydj-music-studio && python3 downloads/ydj_dl_empty.py
```
Run it with `run_in_background`. If there is no saved sign-in, it opens the browser
and waits: tell the user to approve as **ycdupre@gmail.com** (the channel that owns
the playlist). An unverified-app warning is expected: Advanced → Go to ydj-dl.

### Step 3: Confirm
Show the user the "Remove" and "Keep" lists. Point out every "Keep" entry: these were
not downloaded (failed, unavailable, or added since the last `/ydj-dl`). Ask the user
to confirm they have checked the downloads locally and want the "Remove" entries
deleted from the playlist.

### Step 4: Apply (only after explicit confirmation)
```bash
cd /Users/fydupre/Projects/ydj-music-studio && python3 downloads/ydj_dl_empty.py --apply
```
Report how many were removed and any failures. Quota allows about 200 removals per
day; if exhausted, the script stops cleanly and a re-run the next day finishes the job.

## First-time setup (once, by the user)
1. Open https://console.cloud.google.com/ and select the existing project
   **YDJ Music Studio** (ID `ydj-music-studio`) in the top-bar project picker.
2. **APIs & Services → Library** → search "YouTube Data API v3" → **Enable**.
3. **Google Auth Platform** (formerly "OAuth consent screen") → **Get started**:
   app name `ydj-dl`, your email as support/contact, Audience **External**.
4. **Audience → Publish app** (status "In production"). In "Testing", sign-ins expire
   after 7 days. No Google review is needed for personal use.
5. **Clients → Create client** → type **Desktop app** → name `ydj-dl` → Create →
   **Download JSON**.
6. Move it into place and lock it down:
   ```bash
   mv ~/Downloads/client_secret_*.json ~/.shared-scripts/ydj-dl-oauth-client.json
   chmod 600 ~/.shared-scripts/ydj-dl-oauth-client.json
   ```
The first dry run then handles sign-in and saves the refresh token to
`~/.shared-scripts/ydj-dl-oauth-token.json` (0600). To sign in as a different
channel, move that token file to the Trash and re-run.
