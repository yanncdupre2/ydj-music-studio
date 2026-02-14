#!/usr/bin/env python3
"""
Camelot Module

This module defines functions and lookup dictionaries related to the Camelot key system.
It includes functions for parsing Camelot key strings, shifting keys by semitones,
and extracting a key from a comments field. Additionally, it provides a utility function
to print a table of the 24 Camelot keys along with their corresponding real keys and
the keys produced by shifting them by ±1 semitone.
"""

def parse_camelot(camelot_str):
    """Parses a Camelot key string (e.g., '10A') into a tuple: (number, letter)."""
    return int(camelot_str[:-1]), camelot_str[-1]

camelot_to_pitch = {
    "1A": (8, "minor"),
    "1B": (11, "major"),
    "2A": (3, "minor"),
    "2B": (6, "major"),
    "3A": (10, "minor"),
    "3B": (1, "major"),
    "4A": (5, "minor"),
    "4B": (8, "major"),
    "5A": (0, "minor"),
    "5B": (3, "major"),
    "6A": (7, "minor"),
    "6B": (10, "major"),
    "7A": (2, "minor"),
    "7B": (5, "major"),
    "8A": (9, "minor"),
    "8B": (0, "major"),
    "9A": (4, "minor"),
    "9B": (7, "major"),
    "10A": (11, "minor"),
    "10B": (2, "major"),
    "11A": (6, "minor"),
    "11B": (9, "major"),
    "12A": (1, "minor"),
    "12B": (4, "major")
}

pitch_to_camelot = {v: k for k, v in camelot_to_pitch.items()}

def shift_camelot_key(original_key, semitone_shift):
    # Remove any leading zeros, so that "05A" becomes "5A"
    original_key = original_key.lstrip("0")
    if semitone_shift == 0:
        return original_key
    pitch, mode = camelot_to_pitch[original_key]
    new_pitch = (pitch + semitone_shift) % 12
    new_key = pitch_to_camelot.get((new_pitch, mode))
    if new_key is None:
        raise ValueError(f"No mapping for pitch {new_pitch} with mode {mode}")
    return new_key


def extract_key_from_comments(comments):
    """
    Extracts the first token from the Comments field and strips any leading zeros.
    
    For example, "05A some comment" becomes "5A".
    """
    if not comments:
        return None
    token = comments.split()[0]
    return token.lstrip("0")

# Mapping from Camelot keys to corresponding real musical keys.
real_key_mapping = {
    "1A": "Ab minor",
    "1B": "B major",
    "2A": "Eb minor",
    "2B": "F# major",
    "3A": "Bb minor",
    "3B": "Db major",
    "4A": "F minor",
    "4B": "Ab major",
    "5A": "C minor",
    "5B": "Eb major",
    "6A": "G minor",
    "6B": "Bb major",
    "7A": "D minor",
    "7B": "F major",
    "8A": "A minor",
    "8B": "C major",
    "9A": "E minor",
    "9B": "G major",
    "10A": "B minor",
    "10B": "D major",
    "11A": "F# minor",
    "11B": "A major",
    "12A": "C# minor",
    "12B": "E major"
}

def print_camelot_table():
    """
    Prints a table of the 24 Camelot keys.
    
    For each Camelot key, this function prints:
      - The Camelot key.
      - The corresponding real key.
      - The effective key (and real key) obtained by shifting down by 1 semitone.
      - The effective key (and real key) obtained by shifting up by 1 semitone.
    """
    header = f"{'Camelot':^8s} | {'Real Key':^12s} | {'Down Shift':^20s} | {'Up Shift':^20s}"
    print(header)
    print("-" * len(header))
    for num in range(1, 13):
        for letter in ["A", "B"]:
            key = f"{num}{letter}"
            real_key = real_key_mapping.get(key, "N/A")
            key_down = shift_camelot_key(key, -1)
            key_up = shift_camelot_key(key, 1)
            real_key_down = real_key_mapping.get(key_down, "N/A")
            real_key_up = real_key_mapping.get(key_up, "N/A")
            down_str = f"{key_down} ({real_key_down})"
            up_str   = f"{key_up} ({real_key_up})"
            print(f"{key:^8s} | {real_key:^12s} | {down_str:^20s} | {up_str:^20s}")

def get_intermediate_chain(start_key, finish_key):
    """
    Given a start and finish Camelot key (e.g., "4A" and "6A"), returns a list of strings,
    one for each required intermediate step, that describes the acceptable keys for that step.
    
    Allowed transitions: Two keys are considered harmonically matched if their key numbers differ by 0 or 1.
    This function determines the minimal path (using wrap-around on a 12-tone circle) from start to finish,
    and for each intermediate step returns a string like "5A or 5B".
    
    If the two keys are identical, returns an empty list.
    If they are directly adjacent (difference of 1), returns an empty list to indicate no intermediate track is needed.
    Otherwise, returns a list with one element per required intermediate step.
    """
    # Remove any leading zeros.
    start_key = start_key.lstrip("0")
    finish_key = finish_key.lstrip("0")
    
    # Parse keys into number and mode.
    num1, _ = parse_camelot(start_key)
    num2, _ = parse_camelot(finish_key)
    
    # Compute direct distance and wrap-around distance.
    direct_diff = abs(num1 - num2)
    wrap_diff = 12 - direct_diff
    # Choose the smaller distance and determine direction.
    if direct_diff <= wrap_diff:
        distance = direct_diff
        step = 1 if num2 > num1 else -1
    else:
        distance = wrap_diff
        # When using wrap-around, we want to move in the opposite direction.
        step = -1 if num2 > num1 else 1
    
    # If distance is 0, keys are the same; if distance is 1, they are directly adjacent.
    if distance == 0:
        return []
    if distance == 1:
        return []  # No intermediate track is needed.
    
    # Number of intermediate steps required is (distance - 1)
    intermediates = []
    # Start from the start number; generate each intermediate key number along the chosen path.
    current = num1
    for _ in range(distance - 1):
        # Update current by one step modulo 12.
        current = (current + step - 1) % 12 + 1  # Ensures numbers are in 1..12
        # For each intermediate step, both A and B are acceptable.
        intermediates.append(f"{current}A or {current}B")
    return intermediates

def print_harmonic_path_matrix():
    """
    Prints a matrix with rows representing start Camelot keys and columns representing finish Camelot keys.
    
    Each cell in the matrix shows the minimal sequence of intermediate keys required so that a
    transition from the start key to the finish key can be made with only harmonically matched transitions.
    
    If no intermediate track is needed (i.e. the keys are identical), it prints "–".
    If the keys differ by 1 (direct match), it prints "Direct".
    Otherwise, it prints the intermediate keys for each step, separated by a semicolon.
    """
    # Define a standard order of Camelot keys.
    keys = []
    for num in range(1, 13):
        for letter in ["A", "B"]:
            keys.append(f"{num}{letter}")
    
    # Print header row.
    header = "Start\\Finish".ljust(12)
    for finish in keys:
        header += finish.center(20)
    print(header)
    print("-" * len(header))
    
    # For each start key, compute the chain needed for each finish key.
    for start in keys:
        row_str = start.ljust(12)
        for finish in keys:
            if start == finish:
                cell = "–"
            else:
                chain = get_intermediate_chain(start, finish)
                if not chain:
                    # Direct transition (difference of 1)
                    cell = "Direct"
                else:
                    # Join intermediate steps with "; "
                    cell = "; ".join(chain)
            row_str += cell.center(20)
        print(row_str) 


def num_intermediate_tracks(start_key, finish_key):
    """
    Given two Camelot keys (as strings, e.g. "4A" and "6A"), returns the minimum number
    of intermediate tracks required so that the transition from start to finish is harmonically matched.
    
    The effective difference is computed on a circular 12-tone basis.
    If the effective difference is 0 or 1, then no intermediate track is needed.
    Otherwise, the number required is (effective_difference - 1).
    """
    # Remove any leading zeros.
    start_key = start_key.lstrip("0")
    finish_key = finish_key.lstrip("0")
    
    num1, _ = parse_camelot(start_key)
    num2, _ = parse_camelot(finish_key)
    
    diff = abs(num1 - num2)
    eff_diff = min(diff, 12 - diff)
    
    if eff_diff <= 1:
        return 0
    else:
        return eff_diff - 1

def print_harmonic_gap_matrix():
    """
    Prints a matrix with rows representing the start Camelot key and columns representing the finish Camelot key.
    Each cell shows the minimal number of intermediate tracks required for a harmonically matched transition.
    """
    # Generate the standard order of Camelot keys.
    keys = []
    for num in range(1, 13):
        for letter in ["A", "B"]:
            keys.append(f"{num}{letter}")
    
    # Print header row.
    header = "Start\\Finish".ljust(10)
    for finish in keys:
        header += finish.center(10)
    print(header)
    print("-" * len(header))
    
    for start in keys:
        row_str = start.ljust(10)
        for finish in keys:
            if start == finish:
                cell = "0"  # no gap if same key
            else:
                num_needed = num_intermediate_tracks(start, finish)
                cell = str(num_needed)
            row_str += cell.center(10)
        print(row_str)

def print_harmonic_gap_table():
    """
    Prints a table with three columns: Start, Finish, and the number of intermediate tracks needed.
    Only prints each unordered pair once (i.e. if Key1 -> Key2 is printed, then Key2 -> Key1 is omitted).
    """
    # Build the standard ordered list of Camelot keys.
    keys = []
    for num in range(1, 13):
        for letter in ["A", "B"]:
            keys.append(f"{num}{letter}")
    
    # Print header row.
    header = f"{'Start':<8s}  {'Finish':<8s}  {'# Intermediate':<16s}"
    print(header)
    print("-" * len(header))
    
    # For each unordered pair (i < j), compute and print the number of intermediate tracks.
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            start = keys[i]
            finish = keys[j]
            num_needed = num_intermediate_tracks(start, finish)
            print(f"{start:<8s}  {finish:<8s}  {num_needed:<16d}")
            
if __name__ == "__main__":
    print("Camelot table:")
    print_camelot_table()

