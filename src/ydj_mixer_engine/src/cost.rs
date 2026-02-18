/// Edge cost between two tracks using precomputed flat integer tables.
///
/// Mirrors Python's `_fast_edge_cost`:
///   - If |bpm1 - bpm2| > tempo_break_threshold: return tempo_cost_weight * tempo_penalty * tempo_break_factor
///   - Otherwise: look up effective keys via shift_table, then harmonic cost via direct_costs / indirect_costs.
pub struct CostParams {
    pub tempo_threshold: f64,
    pub tempo_penalty: f64,
    pub tempo_break_factor: f64,
    pub tempo_cost_weight: f64,
    pub non_harmonic_cost: f64,
    pub shift_penalty: f64,
    pub shift_weight: f64,
    pub num_keys: usize, // 24
}

impl CostParams {
    pub fn tempo_break_threshold(&self) -> f64 {
        self.tempo_break_factor * self.tempo_threshold
    }
}

/// Compute the combined edge cost (harmonic + weighted tempo) between positions i1 and i2.
///
/// - `shift_table`: flat array of length num_keys * 3, indexed by `key_id * 3 + (shift + 1)`
/// - `direct_costs` / `indirect_costs`: flat arrays of length num_keys^2
#[inline(always)]
pub fn edge_cost(
    i1: usize,
    i2: usize,
    s1: i8,
    s2: i8,
    bpms: &[i32],
    key_ids: &[u8],
    shift_table: &[u8],
    direct_costs: &[f64],
    indirect_costs: &[f64],
    params: &CostParams,
) -> f64 {
    let diff = (bpms[i1] - bpms[i2]).unsigned_abs() as f64;
    let break_thresh = params.tempo_break_threshold();

    if diff > break_thresh {
        return params.tempo_cost_weight * params.tempo_penalty * params.tempo_break_factor;
    }

    // Effective key IDs via shift table
    let ek1 = shift_table[key_ids[i1] as usize * 3 + (s1 + 1) as usize] as usize;
    let ek2 = shift_table[key_ids[i2] as usize * 3 + (s2 + 1) as usize] as usize;
    let idx = ek1 * params.num_keys + ek2;

    let direct = direct_costs[idx];
    let h_cost = if direct == params.non_harmonic_cost && indirect_costs[idx] >= params.non_harmonic_cost {
        direct + 2.0 * params.non_harmonic_cost
    } else {
        direct
    };

    let t_cost = if diff > params.tempo_threshold { params.tempo_penalty } else { 0.0 };

    h_cost + params.tempo_cost_weight * t_cost
}

/// Sum edge costs for all adjacent pairs in the order (full cost scan).
pub fn total_edge_cost(
    order: &[usize],
    shifts: &[i8],
    bpms: &[i32],
    key_ids: &[u8],
    shift_table: &[u8],
    direct_costs: &[f64],
    indirect_costs: &[f64],
    params: &CostParams,
) -> (f64, f64, f64) {
    let n = order.len();
    let mut h_total = 0.0f64;
    let mut t_total = 0.0f64;

    for j in 0..n - 1 {
        let i1 = order[j];
        let i2 = order[j + 1];
        let diff = (bpms[i1] - bpms[i2]).unsigned_abs() as f64;
        let break_thresh = params.tempo_break_threshold();

        if diff > break_thresh {
            t_total += params.tempo_penalty * params.tempo_break_factor;
        } else {
            let ek1 = shift_table[key_ids[i1] as usize * 3 + (shifts[i1] + 1) as usize] as usize;
            let ek2 = shift_table[key_ids[i2] as usize * 3 + (shifts[i2] + 1) as usize] as usize;
            let idx = ek1 * params.num_keys + ek2;
            let direct = direct_costs[idx];
            let h = if direct == params.non_harmonic_cost && indirect_costs[idx] >= params.non_harmonic_cost {
                direct + 2.0 * params.non_harmonic_cost
            } else {
                direct
            };
            h_total += h;
            if diff > params.tempo_threshold {
                t_total += params.tempo_penalty;
            }
        }
    }

    let s_total = params.shift_penalty
        * order.iter().filter(|&&i| shifts[i] != 0).count() as f64;

    (h_total, t_total, s_total)
}

/// Returns the set of edge start-positions (j meaning edge j→j+1) affected by swapping positions a and b.
/// Returned as a small fixed-size array; count indicates how many are valid.
pub fn affected_edges(a: usize, b: usize, n: usize, out: &mut [usize; 4]) -> usize {
    let mut count = 0;
    // Collect unique positions from {a-1, a, b-1, b} that are valid edge indices (0..n-1)
    let mut seen = [usize::MAX; 4];
    for &p in &[a, b] {
        if p > 0 {
            let ep = p - 1;
            if !seen[..count].contains(&ep) {
                seen[count] = ep;
                out[count] = ep;
                count += 1;
            }
        }
        if p < n - 1 {
            let ep = p;
            if !seen[..count].contains(&ep) {
                seen[count] = ep;
                out[count] = ep;
                count += 1;
            }
        }
    }
    count
}

/// Sum costs for the given set of edge positions.
pub fn sum_edge_costs(
    edge_positions: &[usize],
    order: &[usize],
    shifts: &[i8],
    bpms: &[i32],
    key_ids: &[u8],
    shift_table: &[u8],
    direct_costs: &[f64],
    indirect_costs: &[f64],
    params: &CostParams,
) -> f64 {
    edge_positions.iter().map(|&j| {
        edge_cost(
            order[j], order[j + 1],
            shifts[order[j]], shifts[order[j + 1]],
            bpms, key_ids, shift_table, direct_costs, indirect_costs, params,
        )
    }).sum()
}

/// Optimize shift for position `pos` in-place using fast integer lookups.
/// Tries shifts -1, 0, +1 and picks the one minimizing local edge cost.
pub fn optimize_shift_at(
    order: &[usize],
    shifts: &mut [i8],
    pos: usize,
    bpms: &[i32],
    key_ids: &[u8],
    shift_table: &[u8],
    direct_costs: &[f64],
    indirect_costs: &[f64],
    params: &CostParams,
) {
    let i = order[pos];
    let n = order.len();

    let local_cost = |s: i8| -> f64 {
        let mut c = 0.0;
        if pos > 0 {
            c += edge_cost(order[pos - 1], i, shifts[order[pos - 1]], s,
                           bpms, key_ids, shift_table, direct_costs, indirect_costs, params);
        }
        if pos < n - 1 {
            c += edge_cost(i, order[pos + 1], s, shifts[order[pos + 1]],
                           bpms, key_ids, shift_table, direct_costs, indirect_costs, params);
        }
        c
    };

    let current_cost = local_cost(shifts[i]);
    let mut best_s = shifts[i];
    let mut best_cost = current_cost;

    for s in [-1i8, 0, 1] {
        let c = local_cost(s);
        if c < best_cost {
            best_cost = c;
            best_s = s;
        }
    }
    shifts[i] = best_s;
}
