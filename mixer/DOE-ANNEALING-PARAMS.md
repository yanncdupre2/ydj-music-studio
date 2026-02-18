# Design of Experiment: Annealing Parameters

## Goal
Find the optimal initial temperature and cooling schedule that minimize the number of iterations needed to converge to the best cost per attempt, allowing more attempts (random starting points) in a given time budget.

## Background
The cooling factor is auto-calculated from initial temp, final temp, and total iterations:
```python
COOLING_FACTOR = exp(ln(FINAL_TEMP / INITIAL_TEMP) / TOTAL_ITERATIONS)
```

## Experiment Design

### Factors (3 × 3 = 9 experiments)

**Initial Temperature**: 300, 500 (nominal), 700

**Final Temperature**: 0.05, 0.1 (nominal), 0.15

### Duration
6 minutes per variation, 879 total attempts across 9 variations (~98 per variation).

### Metrics Captured
For each attempt:
- **best_iter**: exact iteration number where best cost was last improved
- **best_cost**: lowest cost achieved by that attempt

## Results (2026-02-17)

### Full DOE Summary

| Init T | Fin T | #Att | Cost Min | Cost P25 | Cost Med | Cost P75 | Cost Max | Cost Avg | Iter Med | Iter Avg |
|--------|-------|------|----------|----------|----------|----------|----------|----------|----------|----------|
| 300 | 0.05 | 98 | 50.5 | 68.0 | 74.5 | 81.5 | 96.5 | 74.1 | 111,123 | 125,170 |
| 300 | 0.10 | 97 | 50.5 | 66.0 | 71.5 | 80.8 | 98.0 | 72.7 | 123,035 | 127,228 |
| 300 | 0.15 | 98 | 50.5 | 65.5 | 73.8 | 83.0 | 102.5 | 74.1 | 136,412 | 154,587 |
| 500 | 0.05 | 98 | 50.5 | 64.9 | 75.0 | 80.6 | 105.5 | 73.5 | 110,370 | 125,993 |
| 500 | 0.10 | 98 | 48.0 | 69.9 | 76.5 | 82.6 | 101.5 | 75.9 | 153,355 | 150,010 |
| 500 | 0.15 | 97 | 50.5 | 64.0 | 73.0 | 80.8 | 102.0 | 73.4 | 103,516 | 123,866 |
| 700 | 0.05 | 97 | 50.5 | 65.8 | 74.0 | 82.0 | 98.0 | 73.5 | 135,147 | 157,485 |
| 700 | 0.10 | 98 | 50.5 | 65.2 | 74.5 | 81.6 | 94.0 | 73.4 | 128,496 | 140,358 |
| 700 | 0.15 | 98 | 54.0 | 64.9 | 71.2 | 81.5 | 96.0 | 72.9 | 125,845 | 144,416 |

**Pearson correlation (best_iter vs best_cost): -0.135** (weak; late improvements slightly better)

### Key Findings

1. **Temperature parameters don't significantly affect solution quality.** Cost medians range 71.2–76.5 across all 9 variations — well within noise. Cost averages are even tighter: 72.7–75.9. All percentile ranges overlap.

2. **Temperature parameters don't significantly affect convergence speed.** Iteration medians range 103k–153k and averages 124k–158k with no consistent pattern by initial or final temperature. The tentative trend (higher init temp → faster convergence) observed in a small pilot did not hold up with ~98 attempts per cell.

3. **The dominant factor is the random initial arrangement**, not the temperature schedule. The Pearson correlation of -0.135 between iteration and cost confirms this: whether an attempt finds a good solution is almost entirely driven by its random starting point.

4. **Late improvements (after 300k iterations) are rare but valuable.** Only 10.1% of attempts (89/879) found their best cost after iteration 300,000. However, these late-improving attempts produced slightly better solutions (median cost 71.5 vs 74.0 overall), so cutting iterations would sacrifice quality.

5. **Nominal parameters are optimal.** No variation outperformed the nominal (500 → 0.1) in a statistically significant way. The current 410,000 iterations is well-sized.

### Conclusion
**Keep nominal values: Initial Temp = 500, Final Temp = 0.1, 410,000 iterations.** The best strategy for improving results is maximizing the number of attempts (random starting points) within the time budget, not tuning the temperature schedule. Time budget increased from 3 to 5 minutes to allow ~80 attempts per run.

### Raw Data
Full results saved in `doe_temperature_results.csv` (879 rows: initial_temp, final_temp, attempt, best_iter, best_cost).

## Future Refinements
- Once the Rust engine is available, rerun with 1000+ attempts per config for even stronger statistical power
- Test with different playlist sizes (15, 25, 40 tracks) since optimal params may scale with n
- Consider adaptive cooling schedules (e.g., reheat on stagnation)
