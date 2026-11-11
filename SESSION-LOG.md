# Session Log

## Recent Sessions

### 2026-11-10 — Session close

<!-- gtd-session: fc9f0c1f-eb26-4747-8457-cf0e4f01f329 -->

**Outcomes:**
- Built `pillarbox/` (README there): `scan.py` finds DJ videos whose picture doesn't fill 16:9, `widen.py` crops or non-linearly fills one video, `apply.py` converts library files in place behind a `-backup` copy with a log and restore. Committed in 069d9fb, bf594d2, 7257c56, 9ccdffa.
- Scanned MASTER LIST DJ VIDEO (2,440 entries, 2,368 unique files) in ~7 min: 13 squeezed 5:4 pillarbox, 123 4:3 pillarbox, 198 widescreen letterboxed inside 4:3, 82 other pillarbox, 20 soft/blurred sides, 522 native 4:3 files, 445 letterbox, 952 ok.
- Converted 231 videos in place, all verified before the swap (shown frames, identical audio packets and checksum, identical tags incl. Serato/MIK): 95 near-16:9 letterbox-in-4x3 cropped, 13 pillarbox-5x4 shape-corrected and filled to 1920x1080, 123 pillarbox-4x3 cropped to 4:3. User spot-checked in Music; the 231 backups (13.7 GB) were trashed and the Trash emptied.
- Added `common/playlist_paths.swift` + `get_playlist_file_paths()`: playlist file paths via the iTunesLibrary framework in ~9 s, where Music's `location` over AppleScript takes ~0.2 s per track.
- Logged a Next task to deduplicate MASTER LIST DJ VIDEO and remove or relocate the 4 tracks with missing video files.

**Decisions:**
- Per-category treatment: near-16:9 letterbox-in-4x3 -> crop; pillarbox-5x4 (4:3 PAL that lost its pixel shape) -> correct to 4:3, 5% zoom, cubic non-linear fill (x1.08 centre, x1.95 edge); pillarbox-4x3 -> pure crop at the measured shape, no zoom or stretch, not forced to exactly 1440 wide.
- Library files are replaced at the same path so Apple Music needs no re-import; each original is kept as `<name>-backup` until checked.
- 5:4 band narrowed to 1.20-1.275: pictures measuring 1.275-1.29 are 4:3 with dark edges, not PAL squeeze.
- Verification checks what is played (shown frames, audio packet list + checksum), not container header counts, which old YouTube uploads often get wrong.

**Unresolved:**
- 3 files in MASTER LIST DJ VIDEO have no video stream (Flight Facilities - Down To Earth (Wankelmut Remix), Lost Frequencies ft. Janieck Devy - Reality, Marlon Roudette - When The Beat Drops Out); 2 videos were too dark to classify.
- Love To Go is one of the 9 videos listed 9x in the playlist; possibly related to the open task about two MPEG-4 videos left unwritten.
- Extreme Ways (Bourne identity version) is a 320x172 source; the user plans to delete it.
- The soft-sides detector is about half false positives (lyric videos, plain backgrounds); treat that category as a review list.

**Possible next-session objectives:**
- Audit metadata quality: surface DJ tracks missing BPM or key data (Now top) (recommended)
- Deduplicate MASTER LIST DJ VIDEO and resolve the 4 missing and 3 audio-only video entries
- Decide treatment for the remaining pillarbox candidates
