# Design of Experiment: Annealing Parameters

## Goal
Find the optimal initial temperature and cooling factor that minimize the number of iterations needed to converge to the best cost per attempt. This allows us to reduce iterations per attempt and run more attempts in a given time budget, exploring more random starting points.

## Background
Currently the cooling factor is auto-calculated from initial temp, final temp, and total iterations:
```python
COOLING_FACTOR = exp(ln(FINAL_TEMP / INITIAL_TEMP) / TOTAL_ITERATIONS)
```
For the DOE, we decouple these: cooling factor becomes a fixed independent variable.

## Experiment Design

### Factors (3 × 3 = 9 experiments)

**Initial Temperature** (nominal = 500):
- Low: 375 (−25%)
- Nominal: 500
- High: 625 (+25%)

**Cooling Factor** (nominal ≈ 0.999979, i.e. `exp(ln(0.1/500)/410000)`):
- Fast cooling: nominal × 0.90 (cools 10% faster per step)
- Nominal: current value
- Slow cooling: nominal × 1.10 (cools 10% slower per step, but clamped so factor < 1.0)

Note: "nominal × 0.90" means the exponent (ln of the factor) is scaled by 0.90, making the factor slightly smaller (faster cooling). Concretely:
```python
nominal_factor = exp(ln(0.1 / 500) / 410000)  # ≈ 0.999979
fast_factor = nominal_factor ** 1.1            # smaller, cools faster
slow_factor = nominal_factor ** 0.9            # larger, cools slower
```

### Duration
Each experiment runs for 5 minutes (300 seconds) to get 50+ attempts per configuration.

### Metric to Capture
For each attempt: the **reporting bucket** (0, 50K, 100K, 150K, ..., 400K) at which the best cost was last improved. This tells us after how many iterations convergence typically happens.

## Implementation Plan

### 1. Modify `simulated_annealing_mix()` to accept parameters and return convergence info
Add parameters: `initial_temp`, `cooling_factor` (overriding globals).
Return additional value: `best_found_at_iter` — the iteration bucket (rounded down to nearest `REPORTING_RATE`) where `best_cost` was last updated.

### 2. Create `mixer/doe_annealing.py` script
```python
# Pseudocode
experiments = []
for temp in [375, 500, 625]:
    for cooling_label, cooling_factor in [("fast", fast_cf), ("nominal", nom_cf), ("slow", slow_cf)]:
        results = run_experiment(
            initial_temp=temp,
            cooling_factor=cooling_factor,
            time_limit=300  # 5 minutes
        )
        experiments.append({
            "temp": temp,
            "cooling": cooling_label,
            "attempts": len(results),
            "convergence_buckets": [r.best_found_at for r in results],
            "best_costs": [r.best_cost for r in results],
        })

# Report: for each experiment, show distribution of convergence buckets
# e.g., "Temp=500, Cooling=nominal: 60% converged by 150K, 90% by 250K"
```

### 3. Output format
For each of the 9 experiments, report:
- Number of attempts completed
- Distribution of convergence iteration buckets (histogram)
- Mean and median best cost across attempts
- Mean convergence bucket

### 4. Analysis
The winning configuration is the one where:
1. Most attempts converge early (low mean convergence bucket)
2. Best costs are competitive (not sacrificing quality for speed)

This tells us the optimal `TOTAL_ITERATIONS` to set — e.g., if 90% of attempts converge by 200K, we can set `TOTAL_ITERATIONS = 200000` and run ~2× more attempts in the same time.

## Execution
Run from project root:
```bash
python3 mixer/doe_annealing.py
```
Total runtime: 9 experiments × 5 minutes = ~45 minutes.

## Future Refinements
- Once the Rust engine is available, rerun the DOE with Rust for more statistical power (1000+ attempts per config)
- Test with different playlist sizes (15, 25, 40 tracks) since optimal params may scale with n
- Consider adaptive cooling schedules (e.g., reheat on stagnation)
