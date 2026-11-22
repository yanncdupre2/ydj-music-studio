# TODO — YDJ Music Studio

Backlog for the YDJ Music Studio project. Items are tagged by area:
`[mixer]`, `[library]`, `[downloads]`, `[karaoke]`, `[infra]`.
This file is machine-maintained: `gtd-finish-session` regenerates it. Add, move
or edit tasks through the close request's `task_changes`, never by hand.

## Now

- [ ] [library] Audit metadata quality - surface tracks missing BPM or key data <!-- gtd-task: ae4ffbe7-eac8-46bf-8722-b6b13b282303; next-action: true -->

- [ ] Measure inflow cadence from Apple Music Date Added and re-base the dormancy horizon in PLANNING Inflow [infra] <!-- gtd-task: cb9449a9-af1a-4ef8-8250-896c65b13121 -->

- [ ] In Music, by hand: delete the tracks in playlist "Cloud duplicates to delete" (Option-Delete) and then the playlist; delete the 3 "YDJ restore test" playlists; set artist "Mylène Farmer" on subscription track "XXL (Blue Stahli Remix)" [library] <!-- gtd-task: 0c6e0c18-2faf-47e0-9709-aff440afc63d; outside-session: true -->

## Next

- [ ] Spike: verify AppleScript write support for BPM and Comments (blocks BPM and Camelot-key tagging) [library] <!-- gtd-task: df2b12ee-7a91-45f5-88ad-584eb8d46fc7 -->

- [ ] Investigate why tag_tracks/resolve_tagger left two MPEG-4 videos unwritten (Love To Go, Stronger) before further bulk writes [library] <!-- gtd-task: b4cba746-3846-4943-93ca-c1e43e52a209 -->

- [ ] Download the missing DJ videos: Moon Ray - Comanchero (Video) (re-download) and Avril Lavigne - Sk8er Boi (Video) (iCloud purchase). Then remove the extra 'DJ ÖZGÜR - Comanchero' entry in MASTER LIST DJ VIDEO (kind Music, left by relinking Moon Ray) with Keep File: it shares the real DJ ÖZGÜR file [library] <!-- gtd-task: 00239d2a-640f-4c12-af24-7bdd03c0bebd -->

- [ ] Limit "Genre or Year Blank" (or /fill-missing-genres-years) to the DJ playlists; it now also holds the 1,449 out-of-scope Lefaou imports [library] <!-- gtd-task: 8642754a-ee1e-424d-8520-17d691e7bdb0 -->

## Later

- [ ] Select the mixer input playlist per run instead of the hardcoded "Mixer input" name [mixer] <!-- gtd-task: 52eff23e-87f7-4640-badf-2ad02cb3996f -->

- [ ] [library] BPM detection + tagging for tracks missing tempo data (blocked: no AppleScript BPM write path) <!-- gtd-task: a1bd309c-7461-4c80-bd6f-ffa785dcc737 -->

- [ ] [library] Camelot key detection + tagging into the Comments field (blocked: no AppleScript Comments write path) <!-- gtd-task: 931db6c0-3bc1-4d3a-ac3e-72c9607c86bf -->

- [ ] Remove dead interactive_tagger.py and decide cleanup.py's XML-export dependency [infra] <!-- gtd-task: a853beaa-e632-4c39-9bdd-2d648c387224 -->

- [ ] Decide treatment for the remaining pillarbox candidates: 103 letterbox-in-4x3 not near 16:9, 82 pillarbox-other, 21 soft-sides, and the 4:3 native-narrow files (see pillarbox/data/report.html) [pillarbox] <!-- gtd-task: efab578d-7681-4d88-ab34-d56a96c92c81 -->

- [ ] Fill in the artist on the 247 tracks that have none [library] <!-- gtd-task: 3a0bc72c-f53b-4a1d-aa62-46e41f69b3ac -->

- [ ] Legacy Party Tyme and Sing King workflows: retire them, or fix their known problems: a temp file left in ~/Documents, no -y on the last Party Tyme step, duration cut to whole seconds, hardcoded 1920x1080, an ffmpeg check that does not stop the run, and audio re-encoded instead of copied [karaoke] <!-- gtd-task: 95d62b6e-e66d-4708-b1c5-17410041b12b -->

- [ ] GUI build.sh: move the old app bundle to the Trash instead of rm -rf, and make the install step work when /Applications already has the app [karaoke] <!-- gtd-task: bdc59d55-06ca-4459-b8f4-6454b5962731 -->

## Done

_(empty — checked-off items live here briefly until the next session close drains them into `SESSION-LOG.md`)_
