# Held-Karp Exact Optimizer — Implementation Plan

**Status: PLANNED — implementation deferred**
**Prerequisite: SA engine (`ydj_mixer_engine`) must remain working as fallback**

---

## Why Held-Karp?

The SA engine with 3,561 attempts/5 min still cannot guarantee the global optimum.
With a 17-track playlist, `17! ≈ 3.6 × 10¹⁴` orderings exist; SA samples a tiny fraction.
We know at least one solution with cost 40 exists, yet SA found 48 after 3,561 attempts.

Held-Karp (dynamic programming on bitmask subsets) solves the Hamiltonian Path problem
**exactly** in O(n² · 2ⁿ) time — exponential in n but with a manageable constant.
For n ≤ ~22 tracks it runs in seconds or less; SA remains the engine for larger playlists.

---

## Algorithm

### Problem formulation

Given n tracks, find the ordering π and per-track shifts s ∈ {-1, 0, +1} that minimise:

    total_cost = Σ edge_cost(π[i], π[i+1], s[π[i]], s[π[i+1]])  for i in 0..n-2
               + SHIFT_PENALTY × |{i : s[π[i]] ≠ 0}|

This is a Hamiltonian Path problem (open chain, not a cycle).

### DP state

    dp[mask][last][s_last] = minimum cost to:
        - visit exactly the tracks whose bits are set in `mask`
        - end at track `last` (0-indexed)
        - with shift `s_last` ∈ {-1, 0, +1} for that last track

### Base case (single-track subproblems)

For each starting track i and shift s:

    dp[1 << i][i][s] = SHIFT_PENALTY if s ≠ 0 else 0.0

### Transition

For each state (mask, last, s_last) and each unvisited track j and shift s_j:

    new_mask = mask | (1 << j)
    new_cost = dp[mask][last][s_last]
             + edge_cost(last, j, s_last, s_j)     # harmonic + tempo
             + (SHIFT_PENALTY if s_j ≠ 0 else 0)   # shift penalty for j

    dp[new_mask][j][s_j] = min(dp[new_mask][j][s_j], new_cost)

### Final answer

    best_cost = min over all (last, s_last) of dp[(1<<n)-1][last][s_last]

Backtrack via parent pointers to recover the optimal order and shifts.

---

## Complexity

| n  | States            | Memory (f64) | Ops (~48×states) | Rust time   |
|----|-------------------|-------------|-------------------|-------------|
| 17 | 2¹⁷ × 17 × 3 ≈ 6.7M | ~53 MB      | ~320M             | < 1 s       |
| 20 | 2²⁰ × 20 × 3 ≈ 63M  | ~504 MB     | ~3B               | ~5 s        |
| 22 | 2²² × 22 × 3 ≈ 277M | ~2.2 GB     | ~13B              | ~30–60 s    |
| 24 | 2²⁴ × 24 × 3 ≈ 1.2B | ~9.7 GB     | too slow          | infeasible  |

**Recommended threshold: n ≤ 20 → use Held-Karp; n > 20 → use SA.**

---

## File structure

```
src/ydj_mixer_engine/src/
    lib.rs           # add: optimize_mix_exact() export
    held_karp.rs     # new: DP table, backtracking, parent pointers
    cost.rs          # unchanged (reused)
```

No changes needed to `annealing.rs` — the SA engine is untouched.

---

## API design

New Rust function exposed via PyO3:

```python
optimize_mix_exact(
    bpms:           list[int],
    base_key_ids:   list[int],    # 0-23
    shift_table:    list[int],    # 72 entries (precomputed in Python)
    direct_costs:   list[float],  # 576 entries
    indirect_costs: list[float],  # 576 entries
    cost_params:    dict[str, float],
) -> (best_order: list[int], best_shifts: list[int], best_cost: float, (h, t, s))
```

No time limit parameter — it runs to completion.

### Python dispatch in `mixer.py`

```python
HELD_KARP_MAX_TRACKS = 20

if USE_RUST and n <= HELD_KARP_MAX_TRACKS:
    # Exact global optimum — guaranteed
    order, shifts, cost, (h, t, s) = _rust_optimize_exact(...)
    print(f"Held-Karp exact optimizer: global optimum = {cost:.2f}")
elif USE_RUST:
    # SA for large playlists
    order, shifts, cost, (h,t,s), attempt_costs, n_att, pt_min, pt_max, pt_avg = _rust_optimize_mix(...)
else:
    # Python SA fallback
    ...
```

---

## Implementation steps (when ready)

1. **Add `held_karp.rs`**
   - Allocate `dp: Vec<f64>` of size `(1<<n) * n * 3`, initialised to `f64::INFINITY`
   - Allocate `parent: Vec<(usize, i8)>` same shape for backtracking
   - Fill base cases
   - Iterate over masks in increasing popcount order (ensures dependencies are ready)
   - Find minimum in the full-mask layer; backtrack to recover order and shifts

2. **Export `optimize_mix_exact` in `lib.rs`**
   - Reuse existing `CostParams` builder from `optimize_mix`
   - Return `(Vec<usize>, Vec<i8>, f64, (f64, f64, f64))`

3. **Update `mixer.py` dispatch**
   - Add `try: from ydj_mixer_engine import optimize_mix_exact as _rust_optimize_exact`
   - Add `HELD_KARP_MAX_TRACKS = 20` constant
   - Route based on n and engine availability

4. **Test**
   - Run on current 17-track playlist → verify cost is lower than SA best
   - Confirm backtracked order produces stated cost via Python cost functions

---

## Notes

- The DP table for n=17 is allocated on the heap (`Vec`); no stack overflow risk.
- Iterating masks in popcount order can be done with a standard Gosper's hack or by
  simply iterating 0..(1<<n) (works correctly since smaller subsets always have smaller mask values for any given set of bits — not true in general, but transitions always add a bit so `new_mask > mask` always holds; iterating 0..(1<<n) in order is correct).
- The `edge_cost` function already handles the tempo-break short-circuit and the
  `3×NON_HARMONIC_COST` penalty — no changes needed.
- Memory optimisation (if needed for n > 20): only two mask layers need to be live at once
  (current popcount k and k+1), halving memory. But at n=20 the full table is 504 MB which
  is fine on a modern Mac.
