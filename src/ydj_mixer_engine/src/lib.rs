mod annealing;
mod cost;
mod held_karp;

use pyo3::prelude::*;

use annealing::AnnealingParams;
use cost::CostParams;

/// optimize_mix(bpms, base_key_ids, shift_table, direct_costs, indirect_costs,
///              cost_params, annealing_params, time_limit_secs)
///
/// Runs simulated annealing for `time_limit_secs` seconds (at least one attempt).
///
/// Args (matching precomputed Python tables):
///   bpms           - list[int]   track BPMs (length n)
///   base_key_ids   - list[int]   Camelot key IDs 0-23 (length n)
///   shift_table    - list[int]   72 entries: shift_table[key_id*3+(shift+1)] = eff_key_id
///   direct_costs   - list[float] 576 entries: direct_costs[ek1*24+ek2]
///   indirect_costs - list[float] 576 entries: indirect_costs[ek1*24+ek2]
///   cost_params    - dict[str, float] keys: tempo_threshold, tempo_penalty, tempo_break_factor,
///                                           tempo_cost_weight, non_harmonic_cost,
///                                           shift_penalty, shift_weight
///   annealing_params - dict[str, float] keys: total_iterations, initial_temp, final_temp,
///                                              multi_swap_factor
///   time_limit_secs - float  wall-clock budget in seconds
///
/// Returns:
///   (best_order:     list[int],
///    best_shifts:    list[int],
///    best_cost:      float,
///    cost_breakdown: (h, t, s),
///    attempt_costs:  list[(overall, h, t, s)],
///    n_attempts:     int,
///    per_track_min:  list[float],   # indexed by track index
///    per_track_max:  list[float],
///    per_track_avg:  list[float])
#[pyfunction]
fn optimize_mix(
    bpms: Vec<i32>,
    base_key_ids: Vec<u8>,
    shift_table: Vec<u8>,
    direct_costs: Vec<f64>,
    indirect_costs: Vec<f64>,
    cost_params_dict: std::collections::HashMap<String, f64>,
    annealing_params_dict: std::collections::HashMap<String, f64>,
    time_limit_secs: f64,
) -> PyResult<(
    Vec<usize>, Vec<i8>, f64,
    (f64, f64, f64),
    Vec<(f64, f64, f64, f64)>,
    usize,
    Vec<f64>, Vec<f64>, Vec<f64>,
)> {
    let n = bpms.len();
    if n < 2 {
        return Err(pyo3::exceptions::PyValueError::new_err("Need at least 2 tracks"));
    }

    let get = |d: &std::collections::HashMap<String, f64>, k: &str| -> PyResult<f64> {
        d.get(k).copied().ok_or_else(|| {
            pyo3::exceptions::PyKeyError::new_err(format!("Missing param: {k}"))
        })
    };

    let cp = CostParams {
        tempo_threshold:    get(&cost_params_dict, "tempo_threshold")?,
        tempo_penalty:      get(&cost_params_dict, "tempo_penalty")?,
        tempo_break_factor: get(&cost_params_dict, "tempo_break_factor")?,
        tempo_cost_weight:  get(&cost_params_dict, "tempo_cost_weight")?,
        non_harmonic_cost:  get(&cost_params_dict, "non_harmonic_cost")?,
        shift_penalty:      get(&cost_params_dict, "shift_penalty")?,
        shift_weight:       get(&cost_params_dict, "shift_weight")?,
        num_keys: 24,
    };

    let ap = AnnealingParams {
        total_iterations: get(&annealing_params_dict, "total_iterations")? as usize,
        initial_temp:     get(&annealing_params_dict, "initial_temp")?,
        final_temp:       get(&annealing_params_dict, "final_temp")?,
        multi_swap_factor: get(&annealing_params_dict, "multi_swap_factor")? as usize,
    };

    let (best, attempt_costs, stats) = annealing::run_timed(
        n, &bpms, &base_key_ids, &shift_table, &direct_costs, &indirect_costs,
        &cp, &ap, time_limit_secs,
    );

    let n_attempts = attempt_costs.len();
    Ok((
        best.best_order,
        best.best_shifts,
        best.best_cost,
        (best.h_cost, best.t_cost, best.s_cost),
        attempt_costs,
        n_attempts,
        stats.min,
        stats.max,
        stats.avg,
    ))
}

/// optimize_mix_exact(bpms, base_key_ids, shift_table, direct_costs, indirect_costs, cost_params)
///
/// Runs the Held-Karp exact dynamic-programming algorithm to find the global optimum
/// ordering and per-track shifts.  No time limit — runs to completion.
///
/// Only practical for n ≤ 20 tracks (returns PyValueError for larger playlists).
///
/// Returns:
///   (best_order:     list[int],
///    best_shifts:    list[int],
///    best_cost:      float,
///    cost_breakdown: (h, t, s))
#[pyfunction]
fn optimize_mix_exact(
    bpms: Vec<i32>,
    base_key_ids: Vec<u8>,
    shift_table: Vec<u8>,
    direct_costs: Vec<f64>,
    indirect_costs: Vec<f64>,
    cost_params_dict: std::collections::HashMap<String, f64>,
) -> PyResult<(Vec<usize>, Vec<i8>, f64, (f64, f64, f64))> {
    let n = bpms.len();
    if n < 2 {
        return Err(pyo3::exceptions::PyValueError::new_err("Need at least 2 tracks"));
    }
    if n > 20 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Held-Karp is only supported for n ≤ 20 tracks; use SA for larger playlists",
        ));
    }

    let get = |d: &std::collections::HashMap<String, f64>, k: &str| -> PyResult<f64> {
        d.get(k).copied().ok_or_else(|| {
            pyo3::exceptions::PyKeyError::new_err(format!("Missing param: {k}"))
        })
    };

    let cp = CostParams {
        tempo_threshold:    get(&cost_params_dict, "tempo_threshold")?,
        tempo_penalty:      get(&cost_params_dict, "tempo_penalty")?,
        tempo_break_factor: get(&cost_params_dict, "tempo_break_factor")?,
        tempo_cost_weight:  get(&cost_params_dict, "tempo_cost_weight")?,
        non_harmonic_cost:  get(&cost_params_dict, "non_harmonic_cost")?,
        shift_penalty:      get(&cost_params_dict, "shift_penalty")?,
        shift_weight:       get(&cost_params_dict, "shift_weight")?,
        num_keys: 24,
    };

    let (order, shifts, cost, breakdown) = held_karp::run(
        n, &bpms, &base_key_ids, &shift_table, &direct_costs, &indirect_costs, &cp,
    );

    Ok((order, shifts, cost, breakdown))
}

#[pymodule]
fn ydj_mixer_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(optimize_mix, m)?)?;
    m.add_function(wrap_pyfunction!(optimize_mix_exact, m)?)?;
    Ok(())
}
