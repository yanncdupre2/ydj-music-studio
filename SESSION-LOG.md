# Session Log

## Recent Sessions

### 2026-11-24 — Session close

<!-- gtd-session: 077a0916-f694-4ab0-9c8e-cafe5d1b8fa5 -->

**Outcomes:**
- Rebuilt the venv from a trimmed requirements.txt on python@3.14, at the GAT session's request: 35 packages down to 6 (pandas 3.1.1, numpy 2.5.5, mutagen 1.48.1, maturin 1.16.0); fuzzywuzzy, python-Levenshtein, python-dateutil and pytz left requirements.txt. The old venv is in the Trash as ydj-venv-2026-11 (b9fafb3).
- Moved the mixer engine to pyo3 0.30.1, rand 0.10.4 and rustc 1.100 with no source change (68b88a4). Held-Karp gives identical cost, order and shifts for n = 6-20; SA, which is unseeded, was compared by distribution: 20 alternating runs at n = 40 gave median 147.25 (old) vs 145.5 (new); throughput up 1-5%. Results reported back to GAT.
- Docs: venv setup names python@3.14 because bare python3 is 3.15 with no packages; dependency lists updated; rename_music_file.py's tkinter needs python-tk@3.14, which GAT installed the same day (Tk 9.1) (692ed2f, this close).
- Read-only iTunesLibrary audit of the 8,622 DJ tracks: 0 missing year or genre, taxonomy unchanged (30 strings, 2 known off-taxonomy). 53 tracks lack BPM or a mixer-readable key; 9 of them are deliberate exclusions in playlist "Mixed in Keys Exlusions", leaving 44, 34 never run through Mixed In Key (23fb21b, 3a66a22).
- Measured inflow cadence from Date Added: additions in 29 of the last 36 months, longest lull 4 months (library) and 5 (DJ lists). PLANNING Inflow re-based on it.
- Created playlist "Needs Mixed In Key (2026-11-24)" with the 40 of the 44 that Mixed In Key can analyse; database IDs checked against artist and title, read back live 40 of 40.

**Decisions:**
- BPM and Camelot key come from Mixed In Key, not from this repo (owner, 2026-11-24). The AppleScript BPM/Comments write spike and in-repo BPM and key detection are retired; PLANNING Open Question 3 is resolved.
- Dormancy horizon stays at 12 months, now about 2.5 times the longest measured lull.
- Tracks in "Mixed in Keys Exlusions" (DJ mixes, medleys, full concerts) are left without BPM/key on purpose and are not counted as a gap.

**Completed tasks:**
- [library] Audit metadata quality - surface tracks missing BPM or key data
- Measure inflow cadence from Apple Music Date Added and re-base the dormancy horizon in PLANNING Inflow [infra]

**Dropped tasks:**
- Spike: verify AppleScript write support for BPM and Comments (blocks BPM and Camelot-key tagging) [library]
  - Reason: Superseded: BPM and key come from Mixed In Key (decided 2026-11-24), so no AppleScript BPM/Comments write path is needed.
- [library] BPM detection + tagging for tracks missing tempo data (blocked: no AppleScript BPM write path)
  - Reason: Superseded: Mixed In Key writes BPM; building BPM detection here would duplicate it (decided 2026-11-24).
- [library] Camelot key detection + tagging into the Comments field (blocked: no AppleScript Comments write path)
  - Reason: Superseded: Mixed In Key writes the Camelot key into Comments; building key detection here would duplicate it (decided 2026-11-24).

**Unresolved:**
- Untested whether Mixed In Key's tag writes show up in Music without a refresh; check one track after the MIK pass.
- rename_music_file.py's GUI has not been opened since Tk went from 8.6 to 9.1; launch it once before relying on it.
- The SA engine is unseeded, so future engine upgrades can only be compared by cost distribution, not exact output.

**Possible next-session objectives:**
- Investigate why tag_tracks/resolve_tagger left two MPEG-4 videos unwritten (Love To Go, Stronger) before further bulk writes (recommended)
- Build the repeatable DJ coverage audit, then re-measure BPM/key after the Mixed In Key pass
