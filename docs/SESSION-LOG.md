# Session Log (Archive)

Append-only archive of older dated entries from `PROJECT-LOCAL-CONTEXT.md`'s Recent Sessions log. PLC retains the 5 most recent OR everything from the last 3 months (whichever yields more); entries older than that floor are moved here.

Oldest entries first.

---

### 2026-02-14
- ✅ Built interactive inconsistency resolver (detect → research → fix/ignore per group)
- ✅ Added `add_tracks_to_playlist()` AppleScript capability
- ✅ Created `/resolve-inconsistencies` slash command (229 groups detected in 8,549 DJ tracks)

### 2026-02-15
- ✅ Fixed AppleScript track update reliability with artist+name search fallback
- ✅ Eliminated dependency on fresh XML exports for track updates

### 2026-02-16
- ✅ Added locked fields: consistent metadata preserved, only inconsistent fields resolved
- ✅ Added targeted web search (Source C) for year-only inconsistency groups
- ✅ Resolver displays locked fields with "(locked)" indicator

### 2026-02-17 (morning)
- ✅ Mixer reads from "Mixer input" Apple Music playlist via AppleScript (no hardcoded track list or XML)
- ✅ Added BPM, Comments, Rating fields to `load_playlist_from_app()`
- ✅ Added `load_dj_playlists_from_app()` for candidate library (disabled for now)
- ✅ Time-budgeted optimizer: runs attempts until time limit instead of fixed count
- ✅ Bridge key suggestions for high-cost transitions (shows what keys to look for)
- ✅ 3x penalty for unreachable harmonic transitions
- ✅ SA performance optimization: delta cost (O(1) vs O(n)), integer key IDs, flat cost arrays → 2.8x speedup
- ✅ Created OPTIMIZER-PLAN.md (Python + Rust optimization roadmap)
- ✅ Created DOE-ANNEALING-PARAMS.md (experiment plan for tuning SA parameters)

### 2026-02-17 (evening)
- ✅ DOE for SA annealing parameters completed: 9 variations (init temp 300/500/700 × final temp 0.05/0.1/0.15), 879 total attempts
- ✅ **DOE conclusion**: nominal values (500 → 0.1, 410k iterations) confirmed optimal — no variation statistically better
- ✅ **Key insight**: solution quality is driven by random initial arrangement, not temperature schedule (Pearson r = -0.135)
- ✅ Time budget increased from 3 to 5 minutes (~80 attempts for 17 tracks)
- ✅ DOE results saved to `mixer/doe_temperature_results.csv` (879 rows)
- ✅ `DOE-ANNEALING-PARAMS.md` updated with full findings

### 2026-02-17 (night)
- ✅ **Phase 5: Rust SA engine implemented** (`src/ydj_mixer_engine/`)
- ✅ Rust 1.93.1 + maturin 1.12.2 installed; crate built with PyO3 + rand
- ✅ `optimize_mix()` in Rust: full timed outer loop, delta cost, escape mode, shift optimization
- ✅ Python fallback: `USE_RUST = False` if `ydj_mixer_engine` not importable
- ✅ **Measured speedup: 60x** (Python 0.2 att/s → Rust 12.0 att/s, 17 tracks)
- ✅ Rust finds better solutions (40.5 vs 44.5 best cost in 10s) due to 40x more attempts
- ✅ `.gitignore` updated (Rust `target/`), `requirements.txt` updated (maturin)
- ✅ `OPTIMIZER-PLAN.md` updated with Phase B status and measured results
- **Build command**: `cd src/ydj_mixer_engine && maturin develop --release`

### 2026-02-17 (late night)
- ✅ **Held-Karp exact optimizer implemented** (`src/ydj_mixer_engine/src/held_karp.rs`)
- ✅ DP on bitmask subsets: state (mask, last_track, shift_idx), O(n²·2ⁿ·9)
- ✅ Backtracking without parent table (searches DP table; all costs are exact half-integers)
- ✅ `optimize_mix_exact()` exported via PyO3 in `lib.rs`
- ✅ `mixer.py` dispatch: n ≤ 20 → HK exact; n > 20 → SA; no Rust → Python SA
- ✅ `USE_RUST_EXACT` flag; `HELD_KARP_MAX_TRACKS = 20` constant
- ✅ Verified against brute-force: 20 random tests (n=4–6), all match exactly
- ✅ **Performance: n=17 in 0.43s, n=20 in 4.2s** (global optimum, no time budget needed)
- ✅ **Improved mix output**: bridge hints now appear as `>> ` rows between tracks
  - Both harmonic bridges (h_cost ≥ 5) and tempo bridges (t_cost > 0) shown
  - BPM range = intersection of both neighbors' ±4 BPM windows (correct bridge target)
  - Keys expanded to all ±1 semitone variants (12 keys for 4 effective keys, no spaces around /)
  - Format: `>> [label] - keys: K1/K2(+1)/K3(-1)/... - BPM xxx`
- ✅ `run-mixer.sh`: added `source "$HOME/.cargo/env"` so Rust engine loads correctly
- ✅ `HELD-KARP-PLAN.md` status updated to COMPLETE
- ✅ `OPTIMIZER-PLAN.md` updated with Phase C entry
- **Build command**: `cd src/ydj_mixer_engine && maturin develop --release`

### 2026-02-18
- ✅ **Bridge candidate smart playlists**: 24 key-filter playlists + 24 Candidates playlists created in Apple Music
  - Key-filter naming convention confirmed: `XA or Y(+1) or Z(-1)` where Y/Z are the base keys that reach XA via ±1 semitone shift
  - Example: `6A or 11A(+1) or 1A(-1)` (not `6A(-1)` — the sign indicates the shift applied to the base key)
  - Candidates playlists filter: IN key-filter playlist AND IN "DJ All" AND NOT IN "Mixer input"
  - 22 key-filter playlists created manually; 21 Candidates playlists renamed via AppleScript (`osascript`)
  - `mixer/create_key_playlists.py` written but unused (Apple Music `duplicate` creates regular playlists, not smart ones)
- ✅ **AppleScript rename capability confirmed**: can rename any playlist (smart or regular) via `first playlist whose name is "..."` + `set name`
