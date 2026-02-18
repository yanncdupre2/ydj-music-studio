/// Held-Karp exact dynamic-programming solver for the Hamiltonian Path problem.
///
/// Finds the optimal track ordering and per-track shifts minimising:
///
///   Σ edge_cost(π[i], π[i+1], s[π[i]], s[π[i+1]])   for i in 0..n-2
///   + shift_weight * shift_penalty * |{ i : s[π[i]] ≠ 0 }|
///
/// DP state:
///   dp[mask * n * 3 + last * 3 + s_idx]  =  minimum cost to:
///       • visit exactly the tracks whose bits are set in `mask`
///       • end at track `last`
///       • with shift `s_idx - 1 ∈ {-1, 0, +1}` for that last track
///
/// Time complexity:  O(n² · 2ⁿ · 9)   ≈ O(n² · 2ⁿ)
/// Space complexity: O(n · 2ⁿ · 3)
///
/// Practical limits (rough estimates on Apple Silicon):
///   n ≤ 17 : < 1 s,  ~53 MB
///   n ≤ 20 : ~5 s,  ~503 MB
///   n > 20 : infeasible → use SA instead

use crate::cost::{edge_cost, total_edge_cost, CostParams};

pub fn run(
    n: usize,
    bpms: &[i32],
    key_ids: &[u8],
    shift_table: &[u8],
    direct_costs: &[f64],
    indirect_costs: &[f64],
    params: &CostParams,
) -> (Vec<usize>, Vec<i8>, f64, (f64, f64, f64)) {
    assert!(n >= 1);

    let num_masks = 1usize << n;

    // dp[mask * n * 3 + last * 3 + s_idx] = minimum cost
    // s_idx encodes shift: s_idx = shift + 1, so shift ∈ {-1, 0, +1}
    let mut dp = vec![f64::INFINITY; num_masks * n * 3];

    // Inline index helper (avoids repeated multiply-add in hot path)
    let idx = |mask: usize, last: usize, s_idx: usize| -> usize {
        mask * n * 3 + last * 3 + s_idx
    };

    // Effective shift penalty per shifted track:  shift_weight * shift_penalty
    let eff_sp = params.shift_weight * params.shift_penalty;

    // -----------------------------------------------------------------------
    // Base cases: single-track sub-paths
    // -----------------------------------------------------------------------
    for i in 0..n {
        let mask = 1usize << i;
        for s_idx in 0usize..3 {
            let shift = s_idx as i8 - 1;
            dp[idx(mask, i, s_idx)] = if shift != 0 { eff_sp } else { 0.0 };
        }
    }

    // -----------------------------------------------------------------------
    // DP transitions
    //
    // Iterate masks 1..(1<<n) in ascending order.  Because `new_mask = mask |
    // (1 << j)` always has new_mask > mask (we set a previously-clear bit),
    // smaller masks are always processed before the larger masks that depend on
    // them — so this simple loop ordering is correct.
    // -----------------------------------------------------------------------
    for mask in 1..num_masks {
        for last in 0..n {
            if mask & (1 << last) == 0 {
                continue; // track `last` not in this subset
            }
            for s_idx in 0usize..3 {
                let current = dp[idx(mask, last, s_idx)];
                if current == f64::INFINITY {
                    continue; // unreachable state
                }
                let s_last = s_idx as i8 - 1;

                for j in 0..n {
                    if mask & (1 << j) != 0 {
                        continue; // already visited
                    }
                    let new_mask = mask | (1 << j);

                    for sj_idx in 0usize..3 {
                        let s_j = sj_idx as i8 - 1;
                        let ec = edge_cost(
                            last, j, s_last, s_j,
                            bpms, key_ids, shift_table,
                            direct_costs, indirect_costs, params,
                        );
                        let new_cost = current + ec + if s_j != 0 { eff_sp } else { 0.0 };
                        let t = idx(new_mask, j, sj_idx);
                        if new_cost < dp[t] {
                            dp[t] = new_cost;
                        }
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------------
    // Find the optimal final state
    // -----------------------------------------------------------------------
    let full_mask = num_masks - 1;
    let mut best_cost = f64::INFINITY;
    let mut best_last = 0usize;
    let mut best_s_idx = 1usize; // default: no shift

    for last in 0..n {
        for s_idx in 0usize..3 {
            let c = dp[idx(full_mask, last, s_idx)];
            if c < best_cost {
                best_cost = c;
                best_last = last;
                best_s_idx = s_idx;
            }
        }
    }

    // -----------------------------------------------------------------------
    // Backtrack — no parent table stored; reconstruct by searching the DP.
    //
    // At each step we know (current_mask, current_last, current_s_idx).
    // The previous state has prev_mask = current_mask ^ (1 << current_last).
    // We search all (prev_last, prev_s_idx) in prev_mask for the one that
    // satisfies the DP recurrence (up to floating-point epsilon).
    //
    // All edge costs and shift penalties are exact multiples of 0.5, so f64
    // arithmetic is exact and a tiny epsilon (1e-9) is sufficient.
    // -----------------------------------------------------------------------
    let mut order = Vec::with_capacity(n);
    let mut shifts_out = vec![0i8; n];

    let mut cur_mask = full_mask;
    let mut cur_last = best_last;
    let mut cur_s_idx = best_s_idx;

    loop {
        order.push(cur_last);
        shifts_out[cur_last] = cur_s_idx as i8 - 1;

        if cur_mask.count_ones() == 1 {
            break; // this was the first track
        }

        let cur_cost = dp[idx(cur_mask, cur_last, cur_s_idx)];
        let s_cur = cur_s_idx as i8 - 1;
        let shift_cost_cur = if s_cur != 0 { eff_sp } else { 0.0 };
        let prev_mask = cur_mask ^ (1 << cur_last);

        let mut found = false;
        'search: for prev_last in 0..n {
            if prev_mask & (1 << prev_last) == 0 {
                continue;
            }
            for prev_s_idx in 0usize..3 {
                let prev_cost = dp[idx(prev_mask, prev_last, prev_s_idx)];
                if prev_cost == f64::INFINITY {
                    continue;
                }
                let prev_s = prev_s_idx as i8 - 1;
                let ec = edge_cost(
                    prev_last, cur_last, prev_s, s_cur,
                    bpms, key_ids, shift_table,
                    direct_costs, indirect_costs, params,
                );
                let expected = prev_cost + ec + shift_cost_cur;
                if (expected - cur_cost).abs() < 1e-9 {
                    cur_mask = prev_mask;
                    cur_last = prev_last;
                    cur_s_idx = prev_s_idx;
                    found = true;
                    break 'search;
                }
            }
        }

        if !found {
            // Should never happen with a valid DP table.
            // Break defensively to avoid an infinite loop.
            break;
        }
    }

    // Built from end → start; reverse to get correct order.
    order.reverse();

    // Compute true cost breakdown (harmonic / tempo / shift components).
    let (h, t, s) = total_edge_cost(
        &order, &shifts_out,
        bpms, key_ids, shift_table, direct_costs, indirect_costs, params,
    );

    (order, shifts_out, best_cost, (h, t, s))
}
