use rand::prelude::*;
use rand::rng;

use crate::cost::{
    affected_edges, optimize_shift_at, sum_edge_costs, total_edge_cost, CostParams,
};

pub struct AnnealingParams {
    pub total_iterations: usize,
    pub initial_temp: f64,
    pub final_temp: f64,
    pub multi_swap_factor: usize,
}

impl AnnealingParams {
    pub fn cooling_factor(&self) -> f64 {
        (self.final_temp / self.initial_temp).ln() / self.total_iterations as f64
    }
    pub fn cooling_factor_exp(&self) -> f64 {
        self.cooling_factor().exp()
    }
}

pub struct SaResult {
    pub best_order: Vec<usize>,
    pub best_shifts: Vec<i8>,
    pub best_cost: f64,
    pub h_cost: f64,
    pub t_cost: f64,
    pub s_cost: f64,
}

/// Run a single simulated annealing attempt. Returns the best solution found.
pub fn run_attempt(
    n: usize,
    bpms: &[i32],
    key_ids: &[u8],
    shift_table: &[u8],
    direct_costs: &[f64],
    indirect_costs: &[f64],
    cost_params: &CostParams,
    ann_params: &AnnealingParams,
    rng: &mut impl Rng,
) -> SaResult {
    // Random initial order and shifts
    let mut order: Vec<usize> = (0..n).collect();
    order.shuffle(rng);
    let mut shifts: Vec<i8> = (0..n)
        .map(|_| [-1i8, 0, 1][rng.random_range(0usize..3)])
        .collect();

    // Full cost of initial state
    let (h0, t0, s0) = total_edge_cost(
        &order, &shifts, bpms, key_ids, shift_table, direct_costs, indirect_costs, cost_params,
    );
    let full_cost = |h: f64, t: f64, s: f64| -> f64 {
        h + cost_params.tempo_cost_weight * t + cost_params.shift_weight * s
    };
    let mut best_cost = full_cost(h0, t0, s0);
    let mut best_order = order.clone();
    let mut best_shifts = shifts.clone();
    let mut h_best = h0;
    let mut t_best = t0;
    let mut s_best = s0;

    let mut current_cost = best_cost;
    let cooling = ann_params.cooling_factor_exp();
    let mut temp = ann_params.initial_temp;
    let num_candidates = ann_params.multi_swap_factor * n;

    let mut in_escape_mode = false;
    let mut escape_counter: usize = 0;

    let mut edge_buf = [0usize; 4];

    for master_iter in 0..ann_params.total_iterations {
        if !in_escape_mode {
            // Reset to best known state
            order.copy_from_slice(&best_order);
            shifts.copy_from_slice(&best_shifts);
            current_cost = best_cost;
        }

        // Pick two distinct random positions
        let a = rng.random_range(0..n);
        let mut b = rng.random_range(0..n - 1);
        if b >= a { b += 1; }

        // Affected edges before swap
        let num_affected = affected_edges(a, b, n, &mut edge_buf);
        let affected = &edge_buf[..num_affected];

        let old_edge_cost = sum_edge_costs(
            affected, &order, &shifts, bpms, key_ids, shift_table, direct_costs, indirect_costs, cost_params,
        );

        // Track old shift contributions for the two tracks at positions a and b
        let old_shift_a = shifts[order[a]];
        let old_shift_b = shifts[order[b]];
        let old_shift_count =
            (if old_shift_a != 0 { 1usize } else { 0 }) + (if old_shift_b != 0 { 1 } else { 0 });

        // Perform the swap
        order.swap(a, b);

        // Optimize shifts at both swapped positions
        optimize_shift_at(
            &order, &mut shifts, a,
            bpms, key_ids, shift_table, direct_costs, indirect_costs, cost_params,
        );
        optimize_shift_at(
            &order, &mut shifts, b,
            bpms, key_ids, shift_table, direct_costs, indirect_costs, cost_params,
        );

        // Affected edges after swap
        let new_edge_cost = sum_edge_costs(
            affected, &order, &shifts, bpms, key_ids, shift_table, direct_costs, indirect_costs, cost_params,
        );

        // Shift penalty delta
        let new_shift_a = shifts[order[a]];
        let new_shift_b = shifts[order[b]];
        let new_shift_count =
            (if new_shift_a != 0 { 1usize } else { 0 }) + (if new_shift_b != 0 { 1 } else { 0 });
        let shift_delta = cost_params.shift_penalty * cost_params.shift_weight
            * (new_shift_count as f64 - old_shift_count as f64);

        let candidate_cost = current_cost + (new_edge_cost - old_edge_cost) + shift_delta;

        if candidate_cost < best_cost {
            best_order.copy_from_slice(&order);
            best_shifts.copy_from_slice(&shifts);
            best_cost = candidate_cost;
            current_cost = candidate_cost;
            in_escape_mode = false;
            // Recompute split costs (rare — only on improvement)
            let (h, t, s) = total_edge_cost(
                &best_order, &best_shifts, bpms, key_ids, shift_table, direct_costs, indirect_costs, cost_params,
            );
            h_best = h;
            t_best = t;
            s_best = s;
        } else if in_escape_mode {
            current_cost = candidate_cost;
            escape_counter += 1;
            if escape_counter > num_candidates {
                in_escape_mode = false;
                escape_counter = 0;
            }
        } else {
            let delta = best_cost - candidate_cost; // negative (candidate is worse)
            if (delta / temp).exp() > rng.random::<f64>() {
                in_escape_mode = true;
                escape_counter = 0;
                current_cost = candidate_cost;
            }
        }

        temp *= cooling;
        let _ = master_iter; // suppress lint
    }

    SaResult {
        best_order,
        best_shifts,
        best_cost,
        h_cost: h_best,
        t_cost: t_best,
        s_cost: s_best,
    }
}

/// Run multiple SA attempts until the time budget (seconds) is exhausted.
/// Always runs at least one attempt.
/// Returns the best result across all attempts, plus per-attempt cost breakdown.
pub fn run_timed(
    n: usize,
    bpms: &[i32],
    key_ids: &[u8],
    shift_table: &[u8],
    direct_costs: &[f64],
    indirect_costs: &[f64],
    cost_params: &CostParams,
    ann_params: &AnnealingParams,
    time_limit_secs: f64,
) -> (SaResult, Vec<(f64, f64, f64, f64)>) {
    let mut rng = rng();
    let start = std::time::Instant::now();
    let mut global_best: Option<SaResult> = None;
    let mut attempt_costs: Vec<(f64, f64, f64, f64)> = Vec::new(); // (overall, h, t, s)

    loop {
        let elapsed = start.elapsed().as_secs_f64();
        if attempt_costs.len() > 0 && elapsed >= time_limit_secs {
            break;
        }

        let result = run_attempt(
            n, bpms, key_ids, shift_table, direct_costs, indirect_costs,
            cost_params, ann_params, &mut rng,
        );

        let overall = result.best_cost;
        attempt_costs.push((overall, result.h_cost, result.t_cost, result.s_cost));

        match &global_best {
            None => { global_best = Some(result); }
            Some(prev) if result.best_cost < prev.best_cost => { global_best = Some(result); }
            _ => {}
        }
    }

    (global_best.unwrap(), attempt_costs)
}
