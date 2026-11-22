# Session Log

## Recent Sessions

### 2026-11-22 — Session close

<!-- gtd-session: 9488512f-074e-48c9-ad1e-2d88ca5754f6 -->

**Outcomes:**
- Karaoke tooling moved from the Intel ffmpeg 4.3.1 (/usr/local) to the Apple-silicon ffmpeg 8.1.1 (/opt/homebrew), ahead of removing the Rosetta Homebrew; coordinated with the global-agent-tools session (8d2cfc0). The Party Tyme and both Sing King workflows now call /opt/homebrew/bin/ffmpeg. The GUI no longer puts /usr/local/bin on PATH; it was rebuilt and reinstalled.
- Before the edit, both ffmpeg builds ran every workflow command on a 45 s Britney Spears - Criminal sample. Output matched apart from normal encoder differences. 8.1.1 is 2-5x faster, drops 2 duplicate frames that 4.3.1 added at the end, and with -shortest stops exactly at the end of the audio. After the edit, these passed on 8.1.1: plutil -lint, the commands taken from the edited files, one real Automator run, and a GUI preview and full render.
- Retired two workflow copies whose source is the automator-workflows repo (8d2cfc0, 88a3a06): the interactive ffmpeg workflow (same script as the installed 'Convert Video with ffmpeg') and this repo's older Karaoke Process copy. karaoke-process.md and PROJECT-LOCAL-CONTEXT.md now point to automator-workflows and no longer say to copy the old version over the installed one. The GUI's hint no longer says 'Karaoke Process v2'.

**Decisions:**
- Workflows call ffmpeg by the absolute path /opt/homebrew/bin/ffmpeg, with no /usr/local fallback: Automator's PATH has no Homebrew, and the Intel Homebrew in /usr/local (run under Rosetta) is being removed before macOS 28.
- The automator-workflows repo is the source for installed Quick Actions. This repo keeps no copies of them.
- The three legacy karaoke workflows (Party Tyme, Sing King left and right) stay as runnable references for now. Whether to retire or fix them is a Later task.

**Unresolved:**
- Homebrew's ffmpeg 8.1.1 has no drawtext, subtitles or ass filters. Nothing in this repo uses them.
- /Applications/ffmpeg is a 2020 Intel-only build that stops working when Rosetta goes. Nothing here uses it; the global-agent-tools session removes it once automator-workflows stops using it.
- Moving to ffmpeg 9 is a later, separate step run from global-agent-tools.

**Possible next-session objectives:**
- Run the BPM/Comments AppleScript write spike; it decides whether BPM and Camelot-key tagging can be done at all (recommended)
- Audit which DJ tracks are missing BPM or key
