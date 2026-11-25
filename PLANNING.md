# YDJ Music Studio

## Status
- [ ] Planning
- [x] In Progress
- [ ] On Hold
- [ ] Retired
- [ ] Cancelled

## Project Metadata
- **Project Number:** 02
- **Folder:** `ydj-music-studio`
- **Created:** 2026-02-13
- **Portfolio Area:** Creative & Media
- **Kind:** program

## Objective

Keep the DJ music library continuously enriched and usable for harmonic mixing,
and build the tools that make that work fast enough to sustain.

The Apple Music library holds 20,330 tracks, but the DJ library proper is the
8,622 unique tracks in `MASTER LIST DJ AUDIO` (6,272) and `MASTER LIST DJ VIDEO`
(2,350) — the two playlists used to run a dance party, with no overlap between
them. That subset is where enrichment effort goes and what the Standing
Conditions below are measured against; the rest of the library is not in scope
for tagging. (Counts measured 2026-11-11.)

Library management and enrichment is the ongoing work. Every other area exists
to serve it:

| Area | Role | Reference |
|---|---|---|
| **Library** | Metadata tagging, cleanup, consensus genre/year enrichment — the continuing work | `library-management/README.md` |
| **Mixer** | Harmonic + BPM-continuity playlist optimization over the enriched library | `mixer/README.md` |
| **Downloads** | YouTube acquisition, renaming, and Apple-compatible conversion | `downloads/README.md` |
| **Karaoke** | Video prep for Final Cut Pro overlay blending | `karaoke-processing/karaoke-process.md` |
| **Pillarbox** | Find and fix DJ videos whose picture doesn't fill 16:9 (bars baked in, letterbox inside 4:3) | `pillarbox/README.md` |
| **Delogo** | Erase fixed logos and credit text burned into DJ videos | `delogo/README.md` |
| **Infra** | Shared Apple Music access, genre taxonomy, build environment, write safety | `common/README.md` |

**Why this program has no terminal state.** Music keeps arriving. Every new
track added to the library needs genre, year, BPM and key before it is
mixer-eligible, and there is no state in which the last track has been
acquired. The tools that do the work can be finished; the library they serve
cannot.

## Scope

### In Scope
- Metadata enrichment for the Apple Music library: genre, release year, BPM, Camelot key
- Artist name consistency: one spelling per artist across Artist and Album Artist (added 2026-11-21)
- Consensus tagging from four sources (duplicates, LLM, web, MusicBrainz) and interactive inconsistency resolution
- A canonical 31-genre compound taxonomy (`common/genres.json`)
- Harmonic mixing optimizer using the Camelot wheel and ±1 semitone key shifts
- YouTube acquisition via yt-dlp, renaming to `Artist - Title (type)`, and MKV→MP4 / Opus→AAC conversion
- Karaoke video enhancement for FCP `screen`/`add` overlay blending, CLI plus a macOS GUI front-end
- Video framing repair for `MASTER LIST DJ VIDEO`: detect baked-in bars, then crop or non-linearly fill to 16:9 in place, with audio, timing and DJ cue tags verified unchanged
- Burned-in overlay removal for chosen DJ videos: detect fixed logos and credit text regardless of colour, erase them while on screen, and swap the watched result in place, with audio, timing and DJ cue tags verified unchanged (added 2026-11-20)
- File renaming driven by metadata tags
- Apple Music integration: bulk reads read-only; year and genre writes live and gated per track

### Out of Scope
- Real-time DJ performance tools or live mixing
- Music streaming service integration beyond metadata lookup
- Mobile apps or web interfaces
- Collaborative playlist features

These are standing exclusions, not deferrals. A program has no release to defer
them past; taking one up is a scope change, recorded here with its date.

## Why This Exists

Maintaining a DJ library of this size by hand does not scale:

- Tracks arrive with missing or wrong year, genre, BPM and key, and Apple
  Music's native tools are weak for bulk operations.
- Genre classification is subjective. Compound genres resolve it by design.
- Duplicate and variant tracks drift out of agreement with each other.
- Ordering a set for harmonic and BPM continuity by hand is slow and error-prone.
- YouTube sources and karaoke channels each need format and visual normalization
  before they are usable downstream.

## Strategy and Breakdown

Five areas, no fixed sequencing — each evolves independently. Operational detail
lives in each area's reference, linked in the Objective table above.

### Library — the continuing work
A canonical 31-genre compound taxonomy, 4-source consensus genre/year tagging,
and interactive inconsistency resolution. Live AppleScript reads and writes for
year and genre, in production use.
BPM and Camelot key come from Mixed In Key (see Architecture Decisions).
**Open (measured 2026-11-24):** 43 DJ tracks lack BPM and 49 lack a key the
mixer can read, 53 tracks in all; 39 of them were never run through Mixed In
Key, and 26 arrived in October 2026 or later. The fix is an MIK pass over
new arrivals, not new tooling.

### Mixer — playlist optimization
Harmonic mixing and BPM continuity solved as a track-ordering optimization over
the enriched library. Emits a timestamped Markdown mix report with bridge
key/BPM hints; opt-in `--export` writes the order back as a new playlist.
**Open:** the input playlist name is still hardcoded at `mixer/mixer.py:221`.
The candidate-library tempo-break insertion path remains commented out by design.

### Downloads — YouTube media processing
yt-dlp acquisition (h264/1080p, Safari cookies) → rename using a live Apple
Music artist list → remux and audio conversion for Apple compatibility.
Essentially complete.

### Karaoke — video prep for FCP overlay
A single canonical `karaoke-process` script (bash + ffmpeg) plus a SwiftUI macOS
front-end with live previews and persisted presets. Mature and in use.

### Infra — shared utilities and safety
Shared Apple Music access (`common/`), the genre taxonomy, the Python venv and
Rust build, and library-write safety. Library backup/restore shipped 2026-11-21
(`common/library_backup.py`, see Architecture Decisions).

## Architecture Decisions in Force

Only decisions that still govern current behavior. Superseded reasoning lives in
Git history and `ARCHIVE/SESSION-LOG.md`.

### Compound genre taxonomy
Genres are used exactly as they appear in the library (e.g. `EDM, House, Techno`),
from a canonical list of 31 in `common/genres.json`. This dissolves the "is it
House or Techno?" ambiguity by allowing both, reflects how the music actually
overlaps, and gives an LLM a closed vocabulary to classify into without forcing
false precision. Single-genre and hierarchical taxonomies were both rejected as
poor fits for DJ use.

### Apple Music access: live AppleScript, with one remaining XML reader
Bulk reads and all year/genre writes go through live AppleScript. Reading live
removed the staleness and manual-export burden of the XML workflow.

One consumer still reads the XML export: `library-management/cleanup.py:145`
calls `load_library()`, which reads `~/YDJ Library.xml` via
`common/apple_music.py:8`. That export is absent as of 2026-09-19, so
`cleanup.py` does not run until it is re-exported. Migrating it would remove the
last manual-export dependency.

### The interactive taggers gate every write per track
`tag_tracks.py` and `resolve_tagger.py` are the supported tagging path, and both
put a blocking single-keypress prompt (`1` / `2` / `S`) in front of every live
write and honor `--dry-run`. In `tag_tracks.py` the keypress loop at `:153`, the
identity check at `:178` and the `--dry-run` check at `:188` all precede the
write at `:192` within the same loop iteration; there is no path to the write
that bypasses them. `getch()` calls
`tty.setraw()`, so these scripts require a real TTY — see
`PROJECT-LOCAL-CONTEXT.md` for how to launch them.

**No workflow in this program deletes a library track.** The entire Apple Music
write surface is additive or corrective: `add_tracks_to_playlist()` creates a
new playlist and never mutates an existing one, and the metadata path sets year
and genre. There is no AppleScript `delete` statement anywhere in the tree, and
no command or helper script removes a track. Because the worst outcome is a
mislabeled track rather than a lost one, `--dry-run` plus the per-track keypress
is accepted as sufficient preview and consent, and a separate test library is
not required. This reasoning depends on the no-deletion property, which is
carried as a Standing Condition rather than left as a one-time observation.

The per-track guarantee covers the interactive taggers, not every writer in the tree.
Four other scripts in `library-management/` write to the live library
(`batch_update_no_copyright.py`, `update_year.py`, and two `test_update_hymn*`
scripts), each gated by a single run-level `input()` confirmation rather than
per track. None is part of the documented workflow, but all can write to the
production library, and they are precisely the kind of bulk operation that
should be preceded by a `common/library_backup.py backup`. A fifth,
`interactive_tagger.py`, is dead code and is carried by an [infra] task.

### BPM and Camelot key come from Mixed In Key, not from this repo
Every keyed DJ track carries Mixed In Key's comment form `07A - Energy 7`
(8,573 of 8,573 measured 2026-11-24), and the mixer reads the key from the
first word of Comments (`mixer/camelot.py` `extract_key_from_comments`).
A track with no BPM or no readable key is dropped from the mix with a
warning, not an error. Building BPM detection, key detection or an
AppleScript BPM/Comments write path in this repo would duplicate what Mixed
In Key already does, so all three were retired on 2026-11-24. The cost is a
manual step: new arrivals must be run through Mixed In Key, and the
2026-11-24 audit found 53 DJ tracks that had not been.

### Artist spelling cleanup: consent per artist, backed by backup and journal
`library-management/artist_spellings.py` writes Artist / Album Artist. Unlike the
taggers it takes one keypress per artist in `review`, not per track: an artist
can span 150+ tracks, and the choice is the same for all of them. That is
accepted (2026-11-21) because `apply` adds what the per-track prompt was for:
a fresh library backup first, a check of each track's current value against the
scan, a journal entry before every write, a read-back after it, and `undo`.
`--dry-run` and `--only` (trial runs) precede real runs.

Renaming moves files ("Keep Music Media folder organized" is on), and VirtualDJ
keys cue points by path, so it shows a moved file as a new song without its
cues. Measured in the trial: case-only changes don't move files, accent changes
do. The first run moved 89 files (13 artists). Turning "Keep organized" off
during the cleanup was rejected: folders would keep stale names and files could
move at an unrelated later edit.

**No script edits VirtualDJ's files.** A repair step that rewrote moved paths in
VirtualDJ's `database.xml` was built and removed the same day (2026-11-21). It
read and wrote the file as text, which turned all ~460,000 CRLF line ends into
LF; VirtualDJ judged the database broken, started empty, and on quit saved 8,590
of 54,330 entries. The original was restored from Time Machine. Losing the cue
points of moved files is accepted instead: they are re-checked before each
party anyway. Report which files moved (the journal's paths) rather than
repairing VirtualDJ.

### Library backup: copy what is saved, restore through Choose Library
The library database is held by a background process, AMPLibraryAgent, not by
Music.app (measured 2026-11-21). The agent outlives Music, keeps the library in
memory and saves to the package on disk only now and then. It cannot be
controlled from a script: launchctl refuses to signal it, and SIGTERM sometimes
makes it exit without saving (an unsaved test playlist was lost) and sometimes
is ignored for minutes. Replacing the package's files while it runs does not
work either: the first restore test was overwritten seconds later.

So `common/library_backup.py` never stops the agent and never replaces files
under it. A backup is an APFS clone of the package as last saved, accepted only
if the files are identical before and after the copy, with a manifest of
SHA-256 hashes and the save time (which is what the backup contains). A restore
clones the backup next to the library under a new name and the user switches to
it with Music's Option-launch Choose Library, which makes the agent load it; the
current library stays untouched, so switching back is the undo. Tested end to
end on 2026-11-21: a playlist created after the backup was absent in the
restored library and present again after switching back. File-swap and
agent-signalling restores were both rejected on that evidence.

### Track identification: artist + name, with database ID as fallback
Database IDs are captured at research time and can go stale before the write —
the `/fill-missing-genres-years` workflow can leave hours between the two, and
its `/tmp/recommendations.json` can be resumed a day later. Artist + name
survives that gap; a database ID may not.

Both taggers therefore apply the same two protections. `update_track_metadata()`
takes optional `artist` and `name` and prefers them, falling back to database ID
only when they are absent or the search fails. And before any write, both call
`verify_track()` to confirm the database ID still resolves to the artist and
name the user was shown, skipping loudly on mismatch rather than writing to
whatever the ID now points at. The guard runs in `--dry-run` too, so a preview
surfaces stale IDs before a real run does.

This matters because the keypress prompt identifies a track by artist and name
while the write resolves it by ID. Without the check, approving one track could
write to another.

### Mixer: Rust engine primary, Python fallback
The optimizer's inner loop is Rust via PyO3/maturin; Python owns all I/O and
reporting and passes precomputed flat integer tables. A missing `ydj_mixer_engine`
raises `ImportError` and falls back to the pure-Python loop
(`mixer/mixer.py:13-26`), so the mixer runs on a fresh clone before the Rust
build. Dispatch is by size: `n ≤ 20` uses the Held-Karp exact optimizer
(`HELD_KARP_MAX_TRACKS = 20`, dispatched at `mixer/mixer.py:652`); above that,
time-budgeted simulated annealing. Optimization history is in
`mixer/OPTIMIZER-PLAN.md` and `mixer/DOE-ANNEALING-PARAMS.md`.

### Mixer writes are additive only
`--export` is opt-in and creates a new `Mixer output <timestamp>` playlist. It
never mutates the input playlist. On partial failure it reports added and failed
counts and does not roll back tracks already added.

### Karaoke: one canonical script, channel fit chosen by mode
`karaoke-process` is the single canonical script and binary; the CLI is the path
for batch and scripted use, the GUI for tuning. The core pipeline masks edges,
converts to grayscale, and maps three luminance bands to fixed RGB values, which
makes the output deterministic and therefore predictable under FCP `screen`/`add`
blending.

Channels are handled by choosing a mode rather than by excluding the channel:
`--invert-bands` for channels whose unsung text is brighter than sung text, and
`--no-lut` for multi-color channels where the LUT would flatten distinct singer
colors. Per-channel starting points are in `karaoke-processing/karaoke-process.md`.

### Modular structure with per-area agent context
Each area is a subfolder with its own `CLAUDE.md` for focused agent context;
shared utilities live in `common/`. This keeps the areas independently evolvable
and keeps agent context scoped to the area being worked on.

## Standing Conditions

- **Mixer:** optimizes directly from an Apple Music playlist chosen per run (not a hardcoded name) and writes the result back as a new playlist; exact optimum for n ≤ 20. *Partially met: write-back and exact n ≤ 20 ship; the input playlist name is still the literal "Mixer input" at `mixer/mixer.py:221`. Carried by a [mixer] task.*
- **Library:** <5% of the DJ library missing year/genre; BPM and Camelot key populated for mixer-eligible tracks; consistent compound-genre taxonomy. *Year/genre and taxonomy **met as of 2026-11-24**: across the 8,622 DJ tracks, **0 missing year, 0 missing genre (0.00%)**; 30 genre strings in use, 2 of them off-taxonomy — `Special` (2 tracks, deliberately retained) and `Alternative` (1 track, blocked; see Open Questions). BPM/key **not met**: BPM is absent on 43 tracks (0.50%) and 49 (0.57%) have no key the mixer can read (first word of Comments a valid Camelot key; 45 by the older anywhere-in-Comments pattern). Up from 15 and 17 on 2026-09-19 because recent arrivals skipped Mixed In Key; carried by a [library] task.*
- **Downloads:** files land in Apple-compatible formats with consistent `Artist - Title (type)` names. *Satisfied and stable since 2026-04-28. Qualitative, with no automated check.*
- **Karaoke:** overlays render predictably for FCP `screen`/`add` blending across the channels in use. *Satisfied and stable since 2026-05-09. Qualitative, validated by eye per channel.*
- **Infra:** no data-loss incidents from library writes; backup/restore documented and tested; **no script, command or skill in this program deletes a library track**. *No incidents to date, and the no-deletion property holds as of 2026-09-19. Backup/restore **met 2026-11-21**: `common/library_backup.py`, restore tested end to end through Music's Choose Library switch; a bulk write takes a fresh backup first. The no-deletion condition is what makes `--dry-run` sufficient in place of an isolated test library — if it is ever broken, that decision must be revisited.*

## Inflow

- **Inflow event:** new music added to the Apple Music library that needs
  categorization — genre, release year, BPM or Camelot key. Re-running the
  tagger over already-categorized tracks is this program's own work and is
  **not** inflow.
- **Observed cadence:** roughly monthly, with lulls of up to 4–5 months.
  Measured 2026-11-24 from `Date Added` (`ITLibMediaItem.addedDate` through
  the iTunesLibrary framework) over the 36 months to November 2026: songs and
  music videos were added in 29 of the 36 months (24 with 5 or more adds);
  the longest gap between such months was 4 months for the library and 5 for
  the DJ playlists. This confirms the owner's 2026-10-03 statement. Caveat:
  `Date Added` also moves when a file is re-added, such as a downloaded copy
  replacing a cloud-only duplicate, so some months include re-adds.
- **Dormancy horizon:** 12 months — about two and a half times the longest
  measured lull (re-based 2026-11-24; the value is unchanged). Kept generous
  on purpose: the arrival depends on the owner pulling new music in, so a
  quiet stretch reflects their attention rather than a supply that stopped.
- **Last inflow:** 2026-11-11 — 1,449 MP3s from the Lefaou hard drive added
  to the library (playlist "Lefaou import"), with genre and year left blank
  for categorization. Record only real arrivals here: `P-PLAN-009` reads the
  date and not any caveat, so a proxy such as a commit date counts as an
  arrival.

## Risks and Dependencies

### Risks
1. **Apple Music library corruption** — Impact: high; the library holds 20,330
   tracks, 8,622 of them in the DJ playlists. Bulk reads stay read-only and every live write is gated per track.
   Mitigated since 2026-11-21 by a tested backup/restore (`common/library_backup.py`).
   Residual: a backup holds the library as last saved by AMPLibraryAgent, so
   changes not yet saved are not in it, and with iCloud Sync Library on, Music
   may re-apply cloud changes after switching to an older library.
2. **Genre taxonomy drift** — New genres accumulate inconsistently over time.
   LLM tagging enforces the canonical 31-genre list; periodic audits catch drift.
3. **BPM and key depend on a manual Mixed In Key pass** — nothing in this repo
   writes BPM or Comments, by decision (2026-11-24), so a track that skips
   Mixed In Key stays out of the mixer. This happened to 53 DJ tracks before
   the 2026-11-24 audit. Re-measuring BPM/key coverage at session start or
   after an import catches it.

### Dependencies
- **Apple Music** — macOS-specific; the program is tied to the Apple ecosystem
- **ffmpeg/ffprobe** — required for media processing; installed via Homebrew
- **Python 3.x** — core scripting language; see `requirements.txt`
- **Rust toolchain** — required once to build `ydj_mixer_engine`; the Python optimizer is the fallback when it is not built
- **Mixed In Key** — source of BPM and the Camelot key in Comments; versions 10 and 11 installed, run by hand
- **Apple Music XML export** — still required by `library-management/cleanup.py`; absent as of 2026-09-19

### External APIs
- **MusicBrainz** — integrated (`library-management/sources/musicbrainz.py`, 1 req/sec rate limit)
- Discogs, Spotify, Last.fm — considered, not integrated

## Open Questions

1. **One track cannot be retagged by any supported path.** `61063` Indochine &
   Christine and the Queens - "3SEX" should be `New-Wave, Techno-Pop,
   Electro-Pop, Synth-Pop`, but it is an Apple Music **subscription** track
   (`cloudStatus = subscription`, `.m4p`) and is not reachable through
   `library playlist 1` — neither by database ID nor by artist + name, the two
   lookups every writer uses. It is addressable only via the playlist that
   contains it. Fixing it means editing by hand in Music.app, and the edit may
   not survive a library re-sync. Decide whether subscription tracks are in
   scope for tagging at all; if they are, the write path needs a
   playlist-scoped lookup, which no current code has.

   *Resolved 2026-09-19 — the "smaller genres will be reclassified later"
   commitment that used to sit here. Measurement showed it was not a 44-track
   job: 4 of the 7 sub-threshold strings (`Reggae, Caribbean`, `Comedy`,
   `World`, `Classical, Lyrical`) are canonical master-list genres that are
   simply small inside the DJ subset — `Classical, Lyrical` has 1,459 tracks
   library-wide. Only 5 tracks were off-taxonomy. `K-Pop` (2) was retagged to
   `Pop`, `Special` (2) was deliberately retained as a party-utility category
   with no master-list equivalent, and `Alternative` (1) is the blocked track
   above.*

2. **Taxonomy evolution.** How should new music styles not covered by the 31
   canonical genres be handled — periodic review and expansion, or strict
   enforcement of the existing list?

3. *Resolved 2026-11-24 — BPM and Comments writes.* Not needed. BPM and key
   come from Mixed In Key, and the gap found that day (53 tracks) was new
   arrivals that skipped it, not missing tooling. The AppleScript write spike
   and the in-repo BPM and key detection tasks were retired; see Architecture
   Decisions.

4. **Batch update concurrency.** What is the safe model for batch updates —
   one-at-a-time, batched, or transactional?

5. **Metadata source comparison.** Which external API serves DJ-oriented music
   best, and how should rate limits be handled for large batches?

## Resources & References

- [Apple Music AppleScript Dictionary](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/)
- [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API) · [Discogs API](https://www.discogs.com/developers)
- [Mutagen](https://mutagen.readthedocs.io/) — Python audio metadata
- [beets.io](https://beets.io/) — reference music library manager
- [Camelot Wheel](https://en.wikipedia.org/wiki/Camelot_Wheel) — harmonic mixing system
- [ffmpeg Documentation](https://ffmpeg.org/documentation.html)
