#!/usr/bin/env python3
import os
import math
import random
import copy
import time
import pandas as pd

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from ydj_mixer_engine import optimize_mix as _rust_optimize_mix
    USE_RUST = True
    print("Rust SA engine loaded (ydj_mixer_engine)")
except ImportError:
    USE_RUST = False
    print("Rust SA engine not available — using Python SA loop")

import argparse
_parser = argparse.ArgumentParser(description="YDJ Mixer — playlist optimizer")
_parser.add_argument(
    "minutes", type=float, nargs="?", default=None,
    help=f"Optimization time in minutes (default: {OPTIMIZER_TIME_LIMIT_MINUTES})"
)
_args = _parser.parse_args()
if _args.minutes is not None:
    OPTIMIZER_TIME_LIMIT_MINUTES = _args.minutes
print(f"Time budget: {OPTIMIZER_TIME_LIMIT_MINUTES} min")

from common.apple_music import load_playlist_from_app
from camelot import parse_camelot, shift_camelot_key, extract_key_from_comments, camelot_to_pitch, pitch_to_camelot

import unicodedata


###############################
# Global Parameters for Optimization
###############################

# Cost parameters
TEMPO_THRESHOLD = 4.5
TEMPO_PENALTY = 5
TEMPO_BREAK_FACTOR = 2
TEMPO_COST_WEIGHT = 3

EXACT_MATCH_COST = 0
SAME_KEY_SCALE_CHANGE_COST = 0.5
KEY_DIFF_ONE_COST = 0.5
KEY_DIFF_ONE_SCALE_CHANGE_COST = 5
NON_HARMONIC_COST = 5

SHIFT_PENALTY = 1
SHIFT_WEIGHT = 1

# Annealing parameters

OPTIMIZER_TIME_LIMIT_MINUTES = 5  # run annealing attempts until this time budget is exhausted (minimum 1 attempt)
MULTI_SWAP_FACTOR = 2 # number of times the number of tracks will be attempted to be swapped upon temperature escapes during the anealing iterations

TOTAL_ITERATIONS = 410000
INITIAL_TEMP = 500
FINAL_TEMP = 0.1
REPORTING_RATE = 50000


# Cooling factor is calculated such that the final temperature is reached at TOTAL iterations.
COOLING_FACTOR = math.exp(math.log(FINAL_TEMP / INITIAL_TEMP) / TOTAL_ITERATIONS)


def remove_accents(input_str):
    """
    Normalize the Unicode string to NFKD form and remove diacritical marks.
    For example, 'Mylène' becomes 'Mylene'.
    """
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def normalize_text(text):
    return remove_accents(text).lower()

def harmonic_cost_from_keys(key1, key2):
    """
    Computes the harmonic cost between two Camelot keys (strings) with possible shifts.
    
    Rules:
      - If both the numeric part and the scale (A/B) are identical, return EXACT_MATCH_COST.
      - If the numeric parts are the same but scales differ, return SAME_KEY_SCALE_CHANGE_COST.
      - Otherwise, compute the difference in the numeric parts (taking into account wrap-around,
        e.g., a difference between 12 and 1 is 1). If the difference equals 1, then:
            - Return KEY_DIFF_ONE_COST if the scales match.
            - Return KEY_DIFF_ONE_SCALE_CHANGE_COST if the scales differ.
      - For any larger difference, return NON_HARMONIC_COST.
    
    Note: Leading zeros are stripped so that, for example, "05A" becomes "5A".
    """
    # Remove any leading zeros.
    key1 = key1.lstrip("0")
    key2 = key2.lstrip("0")
    
    # Parse the keys into their numeric and scale components.
    num1, scale1 = parse_camelot(key1)
    num2, scale2 = parse_camelot(key2)
    
    # If both number and scale match, cost is zero.
    if num1 == num2 and scale1 == scale2:
        return EXACT_MATCH_COST
    
    # If numbers match but scales differ, assign a moderate cost.
    if num1 == num2 and scale1 != scale2:
        return SAME_KEY_SCALE_CHANGE_COST
    
    # Compute the absolute difference between key numbers, accounting for circular wrap-around.
    diff = abs(num1 - num2)
    diff = min(diff, 12 - diff)
    
    # If the difference is 1 semitone use the corresponding cost.
    if diff == 1:
        if scale1 == scale2:
            return KEY_DIFF_ONE_COST
        else:
            return KEY_DIFF_ONE_SCALE_CHANGE_COST
    
    # For any larger difference, assign a high dissonance cost.
    return NON_HARMONIC_COST


camelot_keys = [f"{num}{letter}" for num in range(1, 13) for letter in ["A", "B"]]

transition_harmonic_costs = {}
for k1 in camelot_keys:
    transition_harmonic_costs[k1] = {}
    for k2 in camelot_keys:
        direct_cost = harmonic_cost_from_keys(k1, k2)
        # Compute the indirect cost via an intermediate key k3.
        indirect_cost = min(harmonic_cost_from_keys(k1, k3) + harmonic_cost_from_keys(k3, k2)
                            for k3 in camelot_keys)
        transition_harmonic_costs[k1][k2] = (direct_cost, indirect_cost)

# (Optional) Print the matrix — commented out to reduce noise.
# for k1 in camelot_keys:
#     for k2 in camelot_keys:
#         direct, indirect = transition_harmonic_costs[k1][k2]
#         print(f"{k1:4s} -> {k2:4s}: {direct:3.1f},{indirect:3.1f}")

###############################
# Precomputed Integer Tables for Fast SA Loop
###############################

# Map Camelot key strings to integer IDs (0-23)
KEY_TO_ID = {k: i for i, k in enumerate(camelot_keys)}
NUM_KEYS = len(camelot_keys)  # 24

# Shift table: shift_table[key_id * 3 + (shift + 1)] = effective_key_id
# 72 entries covering all (key, shift) combinations
_shift_table = [0] * (NUM_KEYS * 3)
for _kid, _key in enumerate(camelot_keys):
    for _s in (-1, 0, 1):
        _eff = shift_camelot_key(_key, _s)
        _shift_table[_kid * 3 + (_s + 1)] = KEY_TO_ID[_eff]

# Flat cost arrays: direct_cost_flat[ek1 * 24 + ek2] and indirect_cost_flat[ek1 * 24 + ek2]
_direct_cost_flat = [0.0] * (NUM_KEYS * NUM_KEYS)
_indirect_cost_flat = [0.0] * (NUM_KEYS * NUM_KEYS)
for _i, _k1 in enumerate(camelot_keys):
    for _j, _k2 in enumerate(camelot_keys):
        _d, _ind = transition_harmonic_costs[_k1][_k2]
        _direct_cost_flat[_i * NUM_KEYS + _j] = _d
        _indirect_cost_flat[_i * NUM_KEYS + _j] = _ind

# Precompute tempo break threshold
_TEMPO_BREAK_THRESHOLD = TEMPO_BREAK_FACTOR * TEMPO_THRESHOLD


def tempo_cost_value(bpm1, bpm2):
    return 0 if abs(bpm1 - bpm2) <= TEMPO_THRESHOLD else TEMPO_PENALTY


def _fast_edge_cost(i1, i2, s1, s2, bpm_arr, key_id_arr):
    """Compute transition cost between two tracks using integer arrays.

    Returns combined cost (harmonic + weighted tempo). Used in the SA hot loop.
    All lookups are flat array indexing — no string ops or dict hashing.
    """
    diff = abs(bpm_arr[i1] - bpm_arr[i2])
    if diff > _TEMPO_BREAK_THRESHOLD:
        t_cost = TEMPO_PENALTY * TEMPO_BREAK_FACTOR
        return TEMPO_COST_WEIGHT * t_cost
    # Effective key IDs via shift table
    ek1 = _shift_table[key_id_arr[i1] * 3 + (s1 + 1)]
    ek2 = _shift_table[key_id_arr[i2] * 3 + (s2 + 1)]
    idx = ek1 * NUM_KEYS + ek2
    direct = _direct_cost_flat[idx]
    h_cost = direct
    if direct == NON_HARMONIC_COST and _indirect_cost_flat[idx] >= NON_HARMONIC_COST:
        h_cost += 2 * NON_HARMONIC_COST
    t_cost = TEMPO_PENALTY if diff > TEMPO_THRESHOLD else 0
    return h_cost + TEMPO_COST_WEIGHT * t_cost


###############################
# 1. Load Mix Tracks from "Mixer input" Playlist
###############################

print("Loading mix tracks from 'Mixer input' playlist...", flush=True)
mix_input_df = load_playlist_from_app("Mixer input")
print(f"  Found {len(mix_input_df)} tracks in playlist", flush=True)

valid_keys = {"1A","1B","2A","2B","3A","3B","4A","4B","5A","5B","6A","6B","7A","7B","8A","8B","9A","9B","10A","10B","11A","11B","12A","12B"}
mix_tracks_data = []
for _, row in mix_input_df.iterrows():
    key = extract_key_from_comments(row["Comments"])
    if row["BPM"] == 0:
        print(f"WARNING: No BPM for track: {row['Name']} - {row['Artist']}")
        continue
    if key is None or key not in valid_keys:
        print(f"WARNING: No valid key for track: {row['Name']} - {row['Artist']}")
        continue
    mix_tracks_data.append({
        "title": row["Name"],
        "artist": row["Artist"],
        "bpm": row["BPM"],
        "camelot": key
    })
if len(mix_tracks_data) == 0:
    raise ValueError("No valid mix tracks found.")
print(f"  {len(mix_tracks_data)} tracks with valid BPM and Camelot key")

# Build immutable base arrays from mix_tracks_data.
n = len(mix_tracks_data)
base_keys = [track["camelot"] for track in mix_tracks_data]
bpms = [track["bpm"] for track in mix_tracks_data]
# Integer key ID array for the fast SA loop
base_key_ids = [KEY_TO_ID[k] for k in base_keys]

###############################
# 2. Helper Functions (Using Base Arrays, Order, and Shifts)
###############################

def transition_cost_components(i1, i2, s1, s2):
    """
    Given two track indices (i1 and i2) and their respective shift values (s1 and s2),
    compute the harmonic and tempo cost components for the transition from track i1 to i2.
    """
    diff = abs(bpms[i1] - bpms[i2])
    if diff > TEMPO_BREAK_FACTOR * TEMPO_THRESHOLD:
        h_cost = 0
        t_cost = tempo_cost_value(bpms[i1], bpms[i2]) * TEMPO_BREAK_FACTOR
    else:
        key1 = shift_camelot_key(base_keys[i1], s1)
        key2 = shift_camelot_key(base_keys[i2], s2)
        direct,indirect = transition_harmonic_costs[key1][key2]
        h_cost = direct
        # if an indirect transition still won't allow to improve, TRIPLE the harmonic cost
        if direct == NON_HARMONIC_COST and indirect >= NON_HARMONIC_COST:
            h_cost += 2 * NON_HARMONIC_COST
        t_cost = tempo_cost_value(bpms[i1], bpms[i2])
    return h_cost, t_cost

def transition_cost_value(i1, i2, s1, s2):
    h_cost, t_cost = transition_cost_components(i1, i2, s1, s2)
    return h_cost + TEMPO_COST_WEIGHT * t_cost


def total_mix_cost_split_order(order, shifts):
    harmonic_total = 0
    tempo_total = 0
    for j in range(len(order)-1):
        i1 = order[j]
        i2 = order[j+1]
        diff = abs(bpms[i1] - bpms[i2])
        if diff > TEMPO_BREAK_FACTOR * TEMPO_THRESHOLD:
            h_cost = 0
            t_cost = tempo_cost_value(bpms[i1], bpms[i2]) * TEMPO_BREAK_FACTOR
        else:
            k1 = shift_camelot_key(base_keys[i1], shifts[i1])
            k2 = shift_camelot_key(base_keys[i2], shifts[i2])
            direct,indirect = transition_harmonic_costs[k1][k2]
            h_cost = direct
            # if an indirect transition still won't allow to improve, TRIPLE the harmonic cost
            if direct == NON_HARMONIC_COST and indirect >= NON_HARMONIC_COST:
                h_cost += 2 * NON_HARMONIC_COST
            t_cost = tempo_cost_value(bpms[i1], bpms[i2])
        harmonic_total += h_cost
        tempo_total += t_cost
    shift_total = SHIFT_PENALTY * sum(1 for i in order if shifts[i] != 0)
    return harmonic_total, tempo_total, shift_total

def format_effective_key(track, s):
    effective = shift_camelot_key(track['camelot'], s)
    if s == 0:
        return effective
    elif s > 0:
        return f"{effective}[+{s}]"
    else:
        return f"{effective}[{s}]"

def optimize_shift_at(order, shifts, pos):
    """
    Optimize the shift for the track at position 'pos' in the order.
    
    The local cost for the track at position 'pos' is defined as:
      - If pos > 0: the transition cost from the previous track (order[pos-1]) to this track.
      - If pos < len(order)-1: the transition cost from this track to the next track (order[pos+1]).
    
    This function tries each candidate shift (-1, 0, +1) for the track at position 'pos'
    (using the existing shifts for its neighbors) and returns the shift value that minimizes the local cost.
    """
    i = order[pos]  # The track index at position 'pos'
    # Compute the current local cost using the existing shift for track i.
    best_cost = 0
    if pos > 0:
        best_cost += transition_cost_value(order[pos-1], i, shifts[order[pos-1]], shifts[i])
    if pos < len(order)-1:
        best_cost += transition_cost_value(i, order[pos+1], shifts[i], shifts[order[pos+1]])
    best_s = shifts[i]
    # Try each candidate shift (-1, 0, +1).
    for s in [-1, 0, 1]:
        old = shifts[i]
        shifts[i] = s
        candidate_cost = 0
        if pos > 0:
            candidate_cost += transition_cost_value(order[pos-1], i, shifts[order[pos-1]], shifts[i])
        if pos < len(order)-1:
            candidate_cost += transition_cost_value(i, order[pos+1], shifts[i], shifts[order[pos+1]])
        if candidate_cost < best_cost:
            best_cost = candidate_cost
            best_s = s
        shifts[i] = old  # Restore the original value for next candidate.
    # Finally, update the shift for track i to the best candidate.
    shifts[i] = best_s
    return best_s

def _edge_positions_for_swap(a, b, n):
    """Return the set of edge start-positions affected by swapping positions a and b.

    An edge at position j connects order[j] -> order[j+1].
    Swapping positions a and b affects edges that touch either position.
    """
    positions = set()
    for p in (a, b):
        if p > 0:
            positions.add(p - 1)
        if p < n - 1:
            positions.add(p)
    return positions


def _compute_total_cost(order, shifts, bpm_arr, key_id_arr):
    """Compute full cost using fast integer arrays. Returns (total, h, t, s)."""
    h_total = 0.0
    t_total = 0.0
    n = len(order)
    for j in range(n - 1):
        i1, i2 = order[j], order[j + 1]
        diff = abs(bpm_arr[i1] - bpm_arr[i2])
        if diff > _TEMPO_BREAK_THRESHOLD:
            t_total += TEMPO_PENALTY * TEMPO_BREAK_FACTOR
        else:
            ek1 = _shift_table[key_id_arr[i1] * 3 + (shifts[i1] + 1)]
            ek2 = _shift_table[key_id_arr[i2] * 3 + (shifts[i2] + 1)]
            idx = ek1 * NUM_KEYS + ek2
            direct = _direct_cost_flat[idx]
            h = direct
            if direct == NON_HARMONIC_COST and _indirect_cost_flat[idx] >= NON_HARMONIC_COST:
                h += 2 * NON_HARMONIC_COST
            h_total += h
            t_total += TEMPO_PENALTY if diff > TEMPO_THRESHOLD else 0
    s_total = SHIFT_PENALTY * sum(1 for i in range(n) if shifts[i] != 0)
    return h_total + TEMPO_COST_WEIGHT * t_total + SHIFT_WEIGHT * s_total, h_total, t_total, s_total


def _sum_edge_costs(positions, order, shifts, bpm_arr, key_id_arr):
    """Sum the edge costs at given positions."""
    total = 0.0
    for j in positions:
        total += _fast_edge_cost(order[j], order[j + 1], shifts[order[j]], shifts[order[j + 1]], bpm_arr, key_id_arr)
    return total


def _optimize_shift_fast(order, shifts, pos, bpm_arr, key_id_arr):
    """Optimize shift at position pos using fast integer lookups. Modifies shifts in-place."""
    i = order[pos]
    n = len(order)
    best_cost = 0.0
    if pos > 0:
        best_cost += _fast_edge_cost(order[pos - 1], i, shifts[order[pos - 1]], shifts[i], bpm_arr, key_id_arr)
    if pos < n - 1:
        best_cost += _fast_edge_cost(i, order[pos + 1], shifts[i], shifts[order[pos + 1]], bpm_arr, key_id_arr)
    best_s = shifts[i]
    old = shifts[i]
    for s in (-1, 0, 1):
        shifts[i] = s
        cost = 0.0
        if pos > 0:
            cost += _fast_edge_cost(order[pos - 1], i, shifts[order[pos - 1]], s, bpm_arr, key_id_arr)
        if pos < n - 1:
            cost += _fast_edge_cost(i, order[pos + 1], s, shifts[order[pos + 1]], bpm_arr, key_id_arr)
        if cost < best_cost:
            best_cost = cost
            best_s = s
    shifts[i] = best_s


def simulated_annealing_mix():

    n = len(mix_tracks_data)
    bpm_arr = bpms      # module-level list
    key_id_arr = base_key_ids  # module-level list

    # Initialize: random order and shifts
    order = random.sample(range(n), n)
    shifts = [random.choice([-1, 0, 1]) for _ in range(n)]

    # Compute initial full cost
    best_cost, h_best, t_best, s_best = _compute_total_cost(order, shifts, bpm_arr, key_id_arr)

    # Keep best state
    best_order = order[:]
    best_shifts = shifts[:]

    temp = INITIAL_TEMP
    master_iter = 0

    num_candidates = MULTI_SWAP_FACTOR * n
    in_escape_mode = False
    escape_counter = 0

    # Current running cost tracks the state in order/shifts
    current_cost = best_cost

    # MAIN OPTIMIZATION LOOP (delta cost approach)

    while master_iter < TOTAL_ITERATIONS:
        if not in_escape_mode:
            # Reset to best known state
            order[:] = best_order
            shifts[:] = best_shifts
            current_cost = best_cost

        # Pick two random positions and swap
        a, b = random.sample(range(n), 2)

        # Compute cost of affected edges BEFORE the swap
        affected = _edge_positions_for_swap(a, b, n)
        old_edge_cost = _sum_edge_costs(affected, order, shifts, bpm_arr, key_id_arr)

        # Track old shift penalty contribution for the two swapped tracks
        old_shift_a = shifts[order[a]]
        old_shift_b = shifts[order[b]]
        old_shift_count = (1 if old_shift_a != 0 else 0) + (1 if old_shift_b != 0 else 0)

        # Perform the swap
        order[a], order[b] = order[b], order[a]

        # Optimize shifts at the swapped positions
        _optimize_shift_fast(order, shifts, a, bpm_arr, key_id_arr)
        _optimize_shift_fast(order, shifts, b, bpm_arr, key_id_arr)

        # Compute cost of affected edges AFTER the swap + shift optimization
        new_edge_cost = _sum_edge_costs(affected, order, shifts, bpm_arr, key_id_arr)

        # Shift penalty delta
        new_shift_a = shifts[order[a]]
        new_shift_b = shifts[order[b]]
        new_shift_count = (1 if new_shift_a != 0 else 0) + (1 if new_shift_b != 0 else 0)
        shift_delta = SHIFT_PENALTY * SHIFT_WEIGHT * (new_shift_count - old_shift_count)

        # Delta cost
        candidate_cost = current_cost + (new_edge_cost - old_edge_cost) + shift_delta

        if candidate_cost < best_cost:
            best_order[:] = order
            best_shifts[:] = shifts
            best_cost = candidate_cost
            current_cost = candidate_cost
            in_escape_mode = False
            # Recompute split costs for reporting (only on improvement, rare)
            _, h_best, t_best, s_best = _compute_total_cost(best_order, best_shifts, bpm_arr, key_id_arr)
        else:
            if in_escape_mode:
                # Keep exploring — update current_cost for the escape chain
                current_cost = candidate_cost
                escape_counter += 1
                if escape_counter > num_candidates:
                    in_escape_mode = False
                    escape_counter = 0
            else:
                if math.exp((best_cost - candidate_cost) / temp) > random.random():
                    in_escape_mode = True
                    escape_counter = 0
                    current_cost = candidate_cost

        if master_iter % REPORTING_RATE == 0:
            print(f"Iteration {master_iter:6d}: Temp = {temp:.1f}    In Escape Mode: {in_escape_mode}", flush=True)
            print(f"Best   : Overall = {best_cost:5.1f} (H={h_best:5.1f}, T={t_best:5.1f}, S={s_best:5.1f})", flush=True)

        temp *= COOLING_FACTOR
        master_iter += 1

    return best_order, best_shifts, best_cost


###############################
# 4. Candidate Insertion Functions (for Tempo Breaks)
###############################

def find_insertion_candidates(trackA, trackB, candidate_library, tempo_threshold):
    """
    For a transition between trackA and trackB, returns up to 10 candidate songs from candidate_library
    that satisfy:
      1. The candidate's BPM is within the overlapping range of:
            [trackA['bpm'] - tempo_threshold, trackA['bpm'] + tempo_threshold]
         and [trackB['bpm'] - tempo_threshold, trackB['bpm'] + tempo_threshold].
      2. The candidate is harmonically compatible with trackA or trackB.
         For each candidate, we try shifts -1, 0, +1. If one of these yields an effective key
         equal to the effective key of trackA or trackB, we store that optimal shift and effective key.
    """
    low_bound = max(trackA['bpm'] - tempo_threshold, trackB['bpm'] - tempo_threshold)
    high_bound = min(trackA['bpm'] + tempo_threshold, trackB['bpm'] + tempo_threshold)
    if low_bound > high_bound:
        return []
    A_effective = shift_camelot_key(trackA['camelot'], trackA.get('shift', 0))
    B_effective = shift_camelot_key(trackB['camelot'], trackB.get('shift', 0))
    candidates = []
    for candidate in candidate_library:
        cand_bpm = candidate['bpm']
        if not (low_bound <= cand_bpm <= high_bound):
            continue
        optimal_shift = None
        eff_key = None
        for s in [-1, 0, 1]:
            candidate_eff = shift_camelot_key(candidate['camelot'], s)
            if candidate_eff == A_effective or candidate_eff == B_effective:
                optimal_shift = s
                eff_key = candidate_eff
                break
        if optimal_shift is not None:
            cand_copy = candidate.copy()
            cand_copy["optimal_shift"] = optimal_shift
            cand_copy["effective_key"] = eff_key
            candidates.append(cand_copy)
    avg_bpm = (trackA['bpm'] + trackB['bpm']) / 2.0
    candidates.sort(key=lambda c: abs(c['bpm'] - avg_bpm))
    return candidates[:10]


def report_tempo_break_insertions(final_order, final_shifts, candidate_library, tempo_threshold, tempo_break_factor):
    """
    Reports candidate insertion tracks for transitions that exhibit a tempo break.
    
    For each consecutive pair in the final mix (derived from final_order and final_shifts),
    the function computes each track's effective key (base key adjusted by its shift) and
    prints a header line showing the two original tracks (with BPM, original key with shift, and effective key).
    Then, for transitions whose BPM difference is between tempo_threshold and tempo_break_factor * tempo_threshold,
    the function calls find_insertion_candidates and prints a table of candidate tracks with:
      - BPM (formatted as "BPM 115")
      - Original key with optimal shift (e.g. " 7A [-1]")
      - An arrow "->" and then the candidate's effective key
      - The candidate's rating
      - The song title – artist.
    """
    print("\nCandidate insertion tracks for tempo break transitions:")
    final_tracks = []
    for i in final_order:
        track = mix_tracks_data[i].copy()
        track["shift"] = final_shifts[i]
        track["effective_key"] = shift_camelot_key(track["camelot"], track["shift"])
        final_tracks.append(track)
    
    for i in range(len(final_order) - 1):
        trackA = final_tracks[i]
        trackB = final_tracks[i+1]
        diff = abs(trackA['bpm'] - trackB['bpm'])
        if diff > tempo_threshold and diff <= tempo_break_factor * tempo_threshold:
            print(f"\nTransition between:")
            print(f"  {trackA['title']} - {trackA['artist']} | BPM: {trackA['bpm']} | Key: {trackA['camelot']} [{trackA['shift']:+d}] -> {trackA['effective_key']}")
            print(f"  {trackB['title']} - {trackB['artist']} | BPM: {trackB['bpm']} | Key: {trackB['camelot']} [{trackB['shift']:+d}] -> {trackB['effective_key']}")
            
            candidates = find_insertion_candidates(trackA, trackB, candidate_library, tempo_threshold)
            if candidates:
                print(f"{'No.':>3s}  {'BPM':<7s}  {'OrigKey':<10s} -> {'EffKey':<5s}  {'Rating':<8s}  Song - Artist")
                for idx, cand in enumerate(candidates, start=1):
                    bpm_str = f"BPM {cand['bpm']:3d}"
                    key_str = f"{cand['camelot']:>3s} [{cand.get('optimal_shift', 0):+d}]"
                    eff_key_str = f"{cand.get('effective_key', shift_camelot_key(cand['camelot'], 0)):>5s}"
                    rating_str = f"{cand.get('Rating', 'N/A')}"
                    title_artist = f"{cand['title']} - {cand['artist']}"
                    print(f"{idx:2d}. {bpm_str:<7s}  {key_str:<10s} -> {eff_key_str:<5s}  {rating_str:<8s}  {title_artist}")
            else:
                print("   No suitable candidates found.")




# ###############################
# # 5. Build Candidate Library from DJ Playlists (disabled for now)
# ###############################
#
# from common.apple_music import load_dj_playlists_from_app
# print("\nLoading candidate library from DJ playlists...")
# candidate_df = load_dj_playlists_from_app()
# print(f"  Found {len(candidate_df)} tracks in DJ playlists")
# candidate_library = []
# for _, row in candidate_df.iterrows():
#     key = extract_key_from_comments(row["Comments"])
#     if key is None or key not in camelot_to_pitch:
#         continue
#     candidate_library.append({
#         "title": row["Name"],
#         "artist": row["Artist"],
#         "bpm": row["BPM"],
#         "camelot": key,
#         "Rating": row["Rating"]
#     })
# print(f"  {len(candidate_library)} candidates with valid Camelot keys")

###############################
# 6. Run the Optimizer and Report Results
###############################

optimizer_start = time.time()
time_limit_seconds = OPTIMIZER_TIME_LIMIT_MINUTES * 60
per_track_history = []  # list of dicts: track_idx -> avg_total

if USE_RUST:
    # ---------------------------------------------------------------
    # Rust path: pass precomputed tables, run entire time budget in Rust
    # ---------------------------------------------------------------
    _cost_params = {
        "tempo_threshold":    float(TEMPO_THRESHOLD),
        "tempo_penalty":      float(TEMPO_PENALTY),
        "tempo_break_factor": float(TEMPO_BREAK_FACTOR),
        "tempo_cost_weight":  float(TEMPO_COST_WEIGHT),
        "non_harmonic_cost":  float(NON_HARMONIC_COST),
        "shift_penalty":      float(SHIFT_PENALTY),
        "shift_weight":       float(SHIFT_WEIGHT),
    }
    _ann_params = {
        "total_iterations": float(TOTAL_ITERATIONS),
        "initial_temp":     float(INITIAL_TEMP),
        "final_temp":       float(FINAL_TEMP),
        "multi_swap_factor": float(MULTI_SWAP_FACTOR),
    }

    print(f"\nRunning Rust SA engine for {OPTIMIZER_TIME_LIMIT_MINUTES} min...", flush=True)
    (
        global_overall_best_order,
        _best_shifts_raw,
        global_overall_best_cost,
        (h_best_rust, t_best_rust, s_best_rust),
        _attempt_costs,
        _n_attempts,
        _per_track_min,
        _per_track_max,
        _per_track_avg,
    ) = _rust_optimize_mix(
        bpms,
        base_key_ids,
        _shift_table,
        _direct_cost_flat,
        _indirect_cost_flat,
        _cost_params,
        _ann_params,
        float(time_limit_seconds),
    )
    # Rust returns shifts as Vec<i8>; index = track index
    global_overall_best_shifts = list(_best_shifts_raw)

    total_elapsed = time.time() - optimizer_start
    attempt = _n_attempts
    print(f"\nRust engine finished: {attempt} attempts in {total_elapsed:.1f}s", flush=True)
    print(f"Best Overall Cost: {global_overall_best_cost:5.1f}  "
          f"(H={h_best_rust:5.1f}, T={t_best_rust:5.1f}, S={s_best_rust:5.1f})")

    # Report per-attempt costs
    for i, (ov, h, t, s) in enumerate(_attempt_costs, 1):
        print(f"  Attempt {i:3d}: Overall={ov:5.1f}  H={h:5.1f}  T={t:5.1f}  S={s:5.1f}")

    # Encode per-track stats (min/max/avg across all attempts) for the summary table
    # Use a synthetic per_track_history entry with avg, plus direct access to min/max
    _rust_per_track_stats = {i: (_per_track_min[i], _per_track_avg[i], _per_track_max[i])
                             for i in range(n)}  # track_idx -> (min, avg, max)

else:
    # ---------------------------------------------------------------
    # Python fallback path
    # ---------------------------------------------------------------
    global_overall_best_cost = float('inf')
    global_overall_best_order = None
    global_overall_best_shifts = None
    attempt = 0

    while True:
        attempt += 1
        elapsed = time.time() - optimizer_start
        remaining = time_limit_seconds - elapsed
        if attempt > 1 and remaining <= 0:
            break
        print(f"\n--- Annealing Attempt {attempt} (elapsed {elapsed:.0f}s / {time_limit_seconds:.0f}s) ---", flush=True)

        best_order, best_shifts, best_cost = simulated_annealing_mix()
        h, t, s = total_mix_cost_split_order(best_order, best_shifts)
        overall = h + TEMPO_COST_WEIGHT * t + s
        print(f"Attempt {attempt} cost breakdown: Harmonic: {h:5.1f}, Tempo: {t:5.1f}, Shift: {s:5.1f}, Overall: {overall:5.1f}")

        per_track = []
        for pos, idx in enumerate(best_order):
            h_sum = 0.0; t_sum = 0.0; count = 0
            if pos > 0:
                prev_idx = best_order[pos - 1]
                h, t = transition_cost_components(prev_idx, idx, best_shifts[prev_idx], best_shifts[idx])
                h_sum += h; t_sum += t; count += 1
            if pos < n - 1:
                next_idx = best_order[pos + 1]
                h, t = transition_cost_components(idx, next_idx, best_shifts[idx], best_shifts[next_idx])
                h_sum += h; t_sum += t; count += 1
            avg_h = h_sum / count if count else 0.0
            avg_t = t_sum / count if count else 0.0
            per_track.append({"idx": idx, "avg_total": avg_h + TEMPO_COST_WEIGHT * avg_t})
        per_track_history.append({e["idx"]: e["avg_total"] for e in per_track})

        if overall < global_overall_best_cost:
            global_overall_best_cost = overall
            global_overall_best_order = best_order[:]
            global_overall_best_shifts = best_shifts[:]
        print(f"Global Overall Best Cost so far: {global_overall_best_cost:5.1f}")

    total_elapsed = time.time() - optimizer_start
    print(f"\nOptimizer finished: {attempt} attempts in {total_elapsed:.1f}s")

print("\n=== Final Best Overall Results ===")
print(f"Best Overall Cost: {global_overall_best_cost:5.1f}")
h_best, t_best, s_best = total_mix_cost_split_order(global_overall_best_order, global_overall_best_shifts)
print(f"Cost Breakdown: Harmonic: {h_best:5.1f}, Tempo: {t_best:5.1f}, Shift: {s_best:5.1f}")

###############################
# Print out per track costs.
###############################

from collections import defaultdict

# Build summary list — source depends on engine used
summary = []
if USE_RUST:
    # Rust returns pre-aggregated min/max/avg across all attempts
    for idx, (mn, avg, mx) in _rust_per_track_stats.items():
        summary.append((avg, idx, mn, mx, attempt))
else:
    # Python path: aggregate from per_track_history
    track_costs = defaultdict(list)
    for attempt_record in per_track_history:
        for idx, cost in attempt_record.items():
            track_costs[idx].append(cost)
    for idx, costs in track_costs.items():
        mn = min(costs)
        mx = max(costs)
        avg = sum(costs) / len(costs)
        summary.append((avg, idx, mn, mx, len(costs)))

summary.sort(reverse=True, key=lambda x: x[0])  # sort by avg descending

# Print sorted summary table
print("\nPer-track aggregate transition costs over all annealing attempts (sorted worst first):")
print(f"{'Track':<40s} {'Min':>6s} {'Avg':>6s} {'Max':>6s} {'#Runs':>6s}")
for avg, idx, mn, mx, runs in summary:
    title = mix_tracks_data[idx]['title']
    artist = mix_tracks_data[idx]['artist']
    label = f"{title} - {artist}"
    print(f"{label:<40.40s} {mn:6.2f} {avg:6.2f} {mx:6.2f} {runs:6d}")



###############################
# 7. Output the Final Mix with Details
###############################

print("\nFinal Mix Order:")
for pos, idx in enumerate(global_overall_best_order):
    track = mix_tracks_data[idx]
    s = global_overall_best_shifts[idx]
    bpm = track['bpm']
    original_key = track['camelot']
    effective_key = shift_camelot_key(original_key, s)
    
    # Format BPM column: "BPM xxx" in a 7-character field.
    bpm_str = f"BPM {bpm:3d}"
    
    # Format original key with shift in a fixed 10-character field.
    # For example, " 7A [-1]"
    key_str = f"{original_key:>3s} [{s:+d}]"
    
    # Format effective key in a 5-character field.
    eff_key_str = f"{effective_key:>5s}"
    
    # For the first track, display "(Start)". Otherwise, compute transition costs.
    if pos == 0:
        trans_info = "(Start)"
    else:
        prev_idx = global_overall_best_order[pos - 1]
        h_cost, t_cost = transition_cost_components(prev_idx, idx, global_overall_best_shifts[prev_idx], s)
        trans_info = f"(H={h_cost:4.1f}  T={t_cost:4.1f})"
    
    # For high harmonic cost transitions, suggest bridge keys.
    bridge_hint = ""
    if pos > 0:
        prev_idx = global_overall_best_order[pos - 1]
        prev_eff = shift_camelot_key(mix_tracks_data[prev_idx]['camelot'], global_overall_best_shifts[prev_idx])
        if h_cost >= 5:
            suggestions = []
            for candidate_key in camelot_keys:
                for cs in [-1, 0, 1]:
                    candidate_eff = shift_camelot_key(candidate_key, cs)
                    cost_from_prev = transition_harmonic_costs[prev_eff][candidate_eff][0]
                    cost_to_next = transition_harmonic_costs[candidate_eff][effective_key][0]
                    if cost_from_prev <= 0.5 and cost_to_next <= 0.5:
                        suggestions.append(f"{candidate_key}({cs:+d})")
            if suggestions:
                bridge_hint = "  << " + " / ".join(suggestions)

    # Combine all fields in a fixed format.
    print(f"{pos+1:2d}. {bpm_str:<7s}  {key_str:<10s} -> {eff_key_str:<5s}  {trans_info:<20s}  {track['title']} - {track['artist']}{bridge_hint}")




# ###############################
# # 8. Report Candidate Insertions for Tempo Breaks (disabled for now)
# ###############################
#
# report_tempo_break_insertions(global_overall_best_order, global_overall_best_shifts, candidate_library, TEMPO_THRESHOLD, TEMPO_BREAK_FACTOR)
