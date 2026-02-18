# Mixer Optimizer Performance Plan

## Context
The simulated annealing optimizer in `mixer.py` is CPU-bound Python. With 18 tracks and a 3-minute budget, it manages ~19 attempts (410K iterations each). For larger playlists (30+ tracks) this will degrade significantly.

## Performance Profile (per iteration, n tracks)

| Component | % Time | Calls/iter | Issue |
|---|---|---|---|
| `total_mix_cost_split_order()` | ~55% | 1 | Rescans ALL n-1 transitions even though only 2 positions swapped |
| `optimize_shift_at()` × 2 | ~30% | 2 | Up to 32 `shift_camelot_key` calls using string ops + dict hashing |
| List copies (order/shifts) | ~10% | 2-4 | O(n) each, every non-escape iteration |
| RNG, temperature, bookkeeping | ~5% | — | Unavoidable |

Over 410K iterations with 30 tracks: ~37M `shift_camelot_key` calls, ~18.5M `transition_cost_components` calls.

## Phase A: Python-Only Optimizations (5-10x speedup)

### A1. Delta cost evaluation (biggest win)
When swapping positions `a` and `b` in the order, only ~4 transitions change (the edges touching a-1→a, a→a+1, b-1→b, b→b+1). Instead of rescanning all n-1 transitions, compute only the delta. Turns each iteration from O(n) to O(1).

### A2. Integer key IDs instead of strings
Map 24 Camelot keys to integers 0-23. Replace `base_keys: list[str]` with `base_key_ids: list[int]`. Eliminates string hashing in the hot loop.

```python
KEY_TO_ID = {k: i for i, k in enumerate(camelot_keys)}
```

### A3. Precompute shift table as flat array
72-entry lookup: `shift_table[key_id * 3 + (shift+1)] = effective_key_id`. Replaces all `shift_camelot_key()` calls (string lstrip + 2 dict lookups) with one array index.

### A4. Flat cost arrays instead of nested dicts
Replace `transition_harmonic_costs[key1_str][key2_str]` with `direct_cost_flat[ek1 * 24 + ek2]`. Eliminates string hashing on every cost lookup.

### A5. Swap-and-undo instead of list copies
Instead of copying order/shifts every iteration, swap in-place and undo on rejection. Only copy when a new global best is found.

### A6. Merge optimize_shift_at with delta cost
The shift optimization already evaluates local edges. Feed those results directly into the delta cost instead of recomputing in `total_mix_cost_split_order`.

### A7. Minor: precompute `TEMPO_BREAK_FACTOR * TEMPO_THRESHOLD` as constant
Currently recomputed on every call. Value is 9.0 and never changes.

## Phase B: Rust Engine via PyO3 ✅ COMPLETE (60x speedup measured)

Entire SA loop moved to Rust. Python handles I/O (Apple Music, printing), Rust handles compute.

**Measured performance (17 tracks, 10s budget):**
- Python: 0.2 att/s (~3 attempts)
- Rust:  12.0 att/s (~120 attempts)
- Speedup: **60x** in throughput; Rust also finds better solutions due to higher attempt count.

### Architecture
```
src/ydj_mixer_engine/
    Cargo.toml              # pyo3 + rand dependencies
    pyproject.toml          # maturin build config
    src/
        lib.rs              # PyO3 module, exports optimize_mix()
        annealing.rs        # SA loop with delta cost + escape mode, timed outer loop
        cost.rs             # transition cost on integer arrays
```

### API (implemented)
```python
optimize_mix(
    bpms: list[int],
    base_key_ids: list[int],     # 0-23
    shift_table: list[int],      # 72 entries, precomputed in Python
    direct_costs: list[float],   # 576 entries, precomputed in Python
    indirect_costs: list[float], # 576 entries
    cost_params: dict[str, float],
    annealing_params: dict[str, float],
    time_limit_secs: float,
) -> (best_order, best_shifts, best_cost, (h,t,s), attempt_costs, n_attempts)
```

Precomputed tables built in Python (reusing camelot.py), passed as flat arrays. Rust is a pure optimization engine with no Camelot domain knowledge.

### Python Integration (in mixer.py)
```python
try:
    from ydj_mixer_engine import optimize_mix as _rust_optimize_mix
    USE_RUST = True
except ImportError:
    USE_RUST = False  # fallback to Python SA loop
```

### Build
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
pip install maturin
cd src/ydj_mixer_engine && maturin develop --release
```

## Phase C: Held-Karp Exact Optimizer ✅ COMPLETE

For playlists with n ≤ 20 tracks, mixer.py now runs Held-Karp instead of SA, guaranteeing the **global optimum** — something SA cannot do regardless of attempt count.

**Algorithm:** DP on bitmask subsets. State = (mask, last_track, last_shift). Transitions extend the path by one unvisited track with each possible shift, accumulating edge_cost + shift_penalty. Backtracking recovers the optimal order by searching the DP table (no parent table stored).

**Measured performance (Apple Silicon, release build):**
| n  | Time   |
|----|--------|
| 10 | 0.002s |
| 15 | 0.091s |
| 17 | 0.43s  |
| 20 | 4.2s   |

**Files:**
- `src/ydj_mixer_engine/src/held_karp.rs` — new: DP + backtracking
- `src/ydj_mixer_engine/src/lib.rs` — `optimize_mix_exact()` PyO3 export
- `mixer/mixer.py` — dispatch: HK if n≤20 and Rust available, SA otherwise

**Dispatch logic in `mixer.py`:**
```python
HELD_KARP_MAX_TRACKS = 20
if USE_RUST and USE_RUST_EXACT and n <= HELD_KARP_MAX_TRACKS:
    # Held-Karp: exact global optimum
elif USE_RUST:
    # SA: large playlists
else:
    # Python SA fallback
```

## Implementation Order

| Step | What | Speedup | Status |
|---|---|---|---|
| A1 | Delta cost in Python | ~5x | ✅ Done |
| A2-A4 | Integer IDs + flat arrays | ~2x on top | ✅ Done |
| A5-A7 | Swap-undo + minor opts | ~1.5x on top | ✅ Done |
| B | Rust SA engine | 60x total | ✅ Done |
| C | Held-Karp exact optimizer (n≤20) | optimal | ✅ Done |

Phase A achieved 2.8x (combined). Phase B achieves 60x in attempts/second. Phase C guarantees the global optimum for playlists up to 20 tracks.
