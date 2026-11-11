# TODO — YDJ Music Studio

Backlog for the YDJ Music Studio project. Items are tagged by area:
`[mixer]`, `[library]`, `[downloads]`, `[karaoke]`, `[infra]`.
This file is machine-maintained: `gtd-finish-session` regenerates it. Add, move
or edit tasks through the close request's `task_changes`, never by hand.

## Now

- [ ] [library] Audit metadata quality - surface tracks missing BPM or key data <!-- gtd-task: ae4ffbe7-eac8-46bf-8722-b6b13b282303; next-action: true -->

- [ ] Measure inflow cadence from Apple Music Date Added and re-base the dormancy horizon in PLANNING Inflow [infra] <!-- gtd-task: cb9449a9-af1a-4ef8-8250-896c65b13121 -->

## Next

- [ ] Document and test an Apple Music backup/restore workflow before further bulk writes [infra] <!-- gtd-task: 2122c921-ddd8-467d-9fff-fa9b1193096f -->

- [ ] Spike: verify AppleScript write support for BPM and Comments (blocks BPM and Camelot-key tagging) [library] <!-- gtd-task: df2b12ee-7a91-45f5-88ad-584eb8d46fc7 -->

- [ ] Investigate why tag_tracks/resolve_tagger left two MPEG-4 videos unwritten (Love To Go, Stronger) before further bulk writes [library] <!-- gtd-task: b4cba746-3846-4943-93ca-c1e43e52a209 -->

- [ ] Deduplicate MASTER LIST DJ VIDEO (9 videos listed 9x each, e.g. Love To Go) and remove from Music or relocate the 4 tracks whose video files are missing (see pillarbox/data/report.csv) [library] <!-- gtd-task: 0659c94f-912a-4cc6-a723-1dfab1a5d1f3 -->

## Later

- [ ] Select the mixer input playlist per run instead of the hardcoded "Mixer input" name [mixer] <!-- gtd-task: 52eff23e-87f7-4640-badf-2ad02cb3996f -->

- [ ] [library] BPM detection + tagging for tracks missing tempo data (blocked: no AppleScript BPM write path) <!-- gtd-task: a1bd309c-7461-4c80-bd6f-ffa785dcc737 -->

- [ ] [library] Camelot key detection + tagging into the Comments field (blocked: no AppleScript Comments write path) <!-- gtd-task: 931db6c0-3bc1-4d3a-ac3e-72c9607c86bf -->

- [ ] Remove dead interactive_tagger.py and decide cleanup.py's XML-export dependency [infra] <!-- gtd-task: a853beaa-e632-4c39-9bdd-2d648c387224 -->

- [ ] Decide treatment for the remaining pillarbox candidates: 103 letterbox-in-4x3 not near 16:9, 82 pillarbox-other, 21 soft-sides, and the 4:3 native-narrow files (see pillarbox/data/report.html) [pillarbox] <!-- gtd-task: efab578d-7681-4d88-ab34-d56a96c92c81 -->

## Done

_(empty — checked-off items live here briefly until the next session close drains them into `SESSION-LOG.md`)_
