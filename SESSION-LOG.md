# Session Log

## Recent Sessions

### 2026-09-18 — Session close

<!-- gtd-session: 3a7fbaf7-354f-45ba-ba13-e38e5499a152 -->

**Outcomes:**
- Separated session history from operating context: `gtd session migrate-history` moved the 5 Recent Sessions entries out of PROJECT-LOCAL-CONTEXT.md into a new SESSION-LOG.md (latest entry) and ARCHIVE/SESSION-LOG.md (the other 4, joining the 19 already there). All 24 original entries verified byte-identical by per-entry digest; none lost, none duplicated.
- Repointed startup routing: AGENTS.md now sends agents to `gtd session context` for current state plus the latest session entry, keeps the explicit PROJECT-LOCAL-CONTEXT.md reference, and states that no history lives there.
- Corrected stale references across PLC, PLANNING, README, TODO and mixer/CLAUDE.md: the retired `/rebaseline-project` and `/update-project-status` commands, the removed Current Priority mirror, a structure tree listing a nonexistent GEMINI.md plus two never-written TBD modules, and a `docs/SESSION-LOG.md` pointer in the archive preamble.
- Corrected consequential claims against the code rather than the prose: mixer export-back is shipped (opt-in `--export`, mixer/mixer.py:1008), the documented mixer command was replaced with the real `run-mixer.sh` entry point and its time-budget argument, and the tagger's keypress guard was traced to library-management/tag_tracks.py:151 sitting immediately before the live AppleScript write.
- Bounded two overstated claims to their evidence: the 60x mixer speedup is one 2026-02-17 benchmark on a 17-track playlist, not a general guarantee; `--export` reports partial-failure counts and does not roll back tracks already added.
- Reconciled project Claude auto-memory: the Party Tyme chromakey memory said a `--bg-chromakey` flag still had to be built when `--no-lut` + `--bg-color` already shipped, and the preset-storage memory still named the removed `splashEnabled`/`splashSeconds` fields instead of the current intro/outro fields.

**Decisions:**
- Session history is owned by SESSION-LOG.md and ARCHIVE/SESSION-LOG.md; PROJECT-LOCAL-CONTEXT.md holds only current operating knowledge. Agents read `gtd session context` rather than scrolling a log.
- Stale-but-historical text inside archived session entries is preserved verbatim, including a now-broken `docs/SESSION-LOG.md` pointer. The archive's own preamble carries the correction instead, so preservation and accurate navigation do not compete.
- Superseded guidance in PLANNING Notes is marked superseded with its date rather than deleted, so the reason the constraint once existed stays legible.
- Phase-era wording inside Key Decisions and Risks bodies stays untouched, continuing the 2026-05-23 decision to keep those as historical record.

**Unresolved:**
- Standing Condition (Mixer) is only partially met: `--export` and exact n<=20 ship, but the input playlist name is still the literal "Mixer input" at mixer/mixer.py:221. Recorded in PLANNING and carried by a new [mixer] task rather than left implied.
- Standing Condition (Infra) 'backup/restore documented and tested' was unmet with no task carrying it — it had only ever appeared as a possible next-session objective on 2026-06-27. Now carried by a new [infra] task.
- mixer/CLAUDE.md 'Phase 3 priorities' item 4 (visual flow chart of transitions) is unbuilt and has no task. Left as a local wish-list item, deliberately not promoted to a portfolio task.
- PLANNING Inflow still records 'observed cadence: not derivable from this repository'. No ingestion log exists yet, so the quarterly figure remains a stated expectation rather than a measurement.
- Doctrine Compliance stamp added to PLC on 2026-06-14 is no longer present in the file; not restored, since conform-log.md is the surviving record and the conform workflow itself is retired.

**Possible next-session objectives:**
- [infra] Document and test the Apple Music backup/restore workflow - it gates the remaining bulk-write work (recommended)
- [library] Audit metadata quality - surface tracks missing BPM or key data
