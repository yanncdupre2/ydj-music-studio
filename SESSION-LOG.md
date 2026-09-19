# Session Log

## Recent Sessions

### 2026-09-19 — Session close

<!-- gtd-session: 777f5e73-64fe-4593-abb3-e170dbfc6078 -->

**Outcomes:**
- Rewrote PLANNING.md as a current charter: 407 -> 272 lines, validator clean, all six required program sections intact.
- Replaced the 10-entry historical 'Key Decisions and Rationale' narrative with 'Architecture Decisions in Force' - only decisions still governing behavior, each verified against code, with superseded reasoning left to Git and ARCHIVE/SESSION-LOG.md rather than copied into a new historical document.
- Reconciled the XML-vs-AppleScript decision to current reality: live AppleScript is the read and write path; the single remaining XML consumer is cleanup.py:145 via apple_music.py:8, and that export is absent as of 2026-09-19.
- Replaced 'Python First, Rust Later' with the current architecture: Rust inner loop via PyO3, ImportError fallback to pure Python (mixer.py:13-26), Held-Karp exact for n <= 20 (HELD_KARP_MAX_TRACKS=20, dispatched mixer.py:652), time-budgeted SA above.
- Reconciled the karaoke v1/v2 evolution into single current guidance: one canonical script, channel fit chosen by mode (--invert-bands, --no-lut) rather than by declaring channels unsupported - which reverses the 2026-04-28 'not a good fit' caveat that the shipped flags had already made false.
- Restructured the Objective around the program's actual center: library enrichment is the continuing work, and an area table states what each other area contributes and which reference owns its detail.
- Removed superseded annotations, resolved Open Questions #2 and #5, obsolete phase language, and the duplicated Notes section; operational detail now links to its owning reference instead of being restated.
- Corrected a safety claim before it shipped: a draft heading asserted library writes are gated per track and never unattended. Four other scripts in library-management/ write to the live library behind a single run-level input() confirmation, so the guarantee was narrowed to the interactive taggers and the batch writers named.
- Corrected two downstream consumers: PROJECT-LOCAL-CONTEXT.md's Purpose now points at PLANNING's Objective instead of restating a drifted three-domain summary, and README.md's unqualified '60x throughput' claim was bounded to its single 2026-02-17 17-track benchmark, matching the bound already recorded for PLANNING and PLC.

**Decisions:**
- Requirement dispositions: backup-before-bulk-writes -> Standing Condition (Infra) + existing task; read-only-XML-first -> superseded by shipped live writes; Python-first -> satisfied by the Rust port; compound taxonomy, artist+name search, Rust fallback, Held-Karp dispatch, modular per-area context -> verified still in force and retained.
- Three requirements were found unmet with nothing carrying them and were preserved as explicit Open Questions rather than dropped: sub-threshold genre reclassification, the never-built isolated test library, and the uneven track-identity protection between the two taggers.
- No tasks were added and no code was changed. Each preserved obligation is an owner decision about scope or priority, which this cleanup was not authorized to make.
- Verified claims are stated with their evidence and bounded by it; performance figures name their benchmark rather than generalizing.

**Unresolved:**
- Sub-threshold genres: PLC, common/README.md and library-management/CLAUDE.md all promise that <20-song genres 'will be reclassified later'. No task or Standing Condition carries it. Schedule, redefine, or retire.
- Isolated test library: live writes were adopted on the understanding that AppleScript work could be tested against a separate library. It was never built; the keypress gate and --dry-run are preview and consent, not isolation.
- Track-identity protection is uneven: resolve_tagger.py verifies identity via verify_track() and passes artist+name; tag_tracks.py does neither and writes by database ID alone, which is the staleness failure the 2026-02-15 decision was adopted to fix. Both values are in scope at tag_tracks.py:137.
- Four run-level-gated batch writers can still write to the production library outside the documented workflow; the outstanding backup/restore condition is what covers them.
- Inflow cadence, the BPM/Comments write path, and the Library <5% measurement remain open and are carried by existing Now/Next tasks.

**Possible next-session objectives:**
- [infra] Measure inflow cadence from Apple Music Date Added and re-base the dormancy horizon (recommended)
- Decide the three preserved obligations: sub-threshold genres, isolated test library, tagger identity protection
