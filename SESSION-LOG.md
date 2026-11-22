# Session Log

## Recent Sessions

### 2026-11-21 — Session close

<!-- gtd-session: cfc736ed-da14-44c3-88f1-c6085fe44a99 -->

**Outcomes:**
- Delogo shipped (852cfbb): `delogo/delogo.py` finds fixed overlays of any colour (edges that hold still while the picture changes), tracks when each is on screen and erases it with ffmpeg removelogo; `pillarbox/apply.py --delogo` swaps a reviewed render in place. Erasure "Oh L'Amour" done.
- rename_youtube: the karaoke cleanup no longer eats the artist or title, and exact artist matches take the library's spelling (417ea8e, 2b69819). Two /ydj-dl runs renamed and imported.
- Library backup/restore shipped and tested end to end (b16e6c8): `common/library_backup.py` backs up and verifies the library; restore goes through Music's Choose Library.
- Artist spelling cleanup (1a550a7): `library-management/artist_spellings.py` with per-artist review against MusicBrainz, a journal and undo. 81 artists and 714 tracks changed, 89 files moved. On 2026-11-22 Björk was switched back to the accented spelling (15 files moved).
- VirtualDJ incident: the cleanup's VirtualDJ step rewrote database.xml with LF line endings. VirtualDJ set it aside as broken and the user restored the 2026-10-15 copy from Time Machine. The step was removed and scripts no longer edit VirtualDJ files.
- Cloud-only duplicates: the 23 "File permission error (-54)" refusals are cloud-only copies of local files that were already fixed. 151 cloud duplicates found. Their downloaded copies were added to the playlists only the cloud copy was in (22 additions) and given the cloud copy's higher stars (7 tracks). All 151 are in the playlist "Cloud duplicates to delete".

**Decisions:**
- Delogo is a separate tool. apply.py --delogo only swaps in a render the user has watched; it never renders one itself.
- Restore goes through Music's Choose Library, never by copying files back: AMPLibraryAgent overwrote a file-level restore.
- Artist spellings are approved one artist at a time, with a backup taken first and every write journaled for undo.
- Scripts never edit VirtualDJ's database.xml or lists. Cue points lost when files move are accepted.
- Cloud-only duplicates are not downloaded, since that would only duplicate local files. Their playlists and stars are carried to the downloaded copy, and the user deletes them by hand.

**Completed tasks:**
- Document and test an Apple Music backup/restore workflow before further bulk writes [infra]

**Unresolved:**
- Deletions by hand in Music: the 151 tracks in "Cloud duplicates to delete" (then the playlist itself) and the 3 "YDJ restore test" playlists. Also by hand: set the artist on subscription track Mylene Farmer "XXL (Blue Stahli Remix)".
- 22 cloud-only tracks share a title with a downloaded track but differ in length; not reviewed.
- 247 tracks have no artist.
- 4 library backups, 2.0 GB, in ~/Music/Music/YDJ Library Backups. Keep the newest and move the older ones to the Trash once the artist changes are confirmed.
- VirtualDJ appeared to re-read cue points from file tags for two moved videos; not confirmed.
- Delogo falsely flags static scenes with flickering light; use --skip.

**Possible next-session objectives:**
- Run the BPM/Comments AppleScript write spike; it decides whether BPM and Camelot-key tagging can be done at all (recommended)
- Audit which DJ tracks are missing BPM or key
