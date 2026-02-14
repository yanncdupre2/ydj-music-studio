#!/usr/bin/env python3
"""Genre mapping and consensus logic.

Maps external genre strings to the 31 YDJ canonical genres via
exact match → substring match → fuzzy threshold (0.5).

Import:
    from sources.genre_mapper import map_genre_to_ydj, determine_consensus
"""
import json
import os

# Load YDJ canonical genres
GENRES_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'common', 'genres.json')
with open(GENRES_PATH, 'r') as f:
    YDJ_GENRES = json.load(f)


def map_genre_to_ydj(external_genre):
    """Map an external genre string to the best-matching YDJ canonical genre.

    Strategy: exact match → substring match → None (if best score <= 0.5).
    Returns the YDJ genre string or None.
    """
    if not external_genre:
        return None

    external_lower = external_genre.lower()

    # Exact match
    for ydj_genre in YDJ_GENRES:
        if external_lower == ydj_genre.lower():
            return ydj_genre

    # Substring / component match
    best_match = None
    best_score = 0.0

    for ydj_genre in YDJ_GENRES:
        components = [c.strip().lower() for c in ydj_genre.split(',')]
        for component in components:
            if component in external_lower or external_lower in component:
                score = len(component) / max(len(external_lower), len(component))
                if score > best_score:
                    best_score = score
                    best_match = ydj_genre

    return best_match if best_score > 0.5 else None


def determine_consensus(sources):
    """Determine year/genre recommendations from all available sources.

    Args:
        sources: dict with keys like 'source_a', 'source_b', 'source_c', 'source_d'.
            Each value is a dict with 'year' and 'genre'/'genres' (or None).

    Returns:
        dict with keys: year, genre_primary, genre_alternate, confidence.
    """
    # Collect years
    years = []
    for source_data in sources.values():
        if source_data and source_data.get('year'):
            years.append(source_data['year'])

    consensus_year = max(set(years), key=years.count) if years else None

    # Collect and map genres
    ydj_genres = []
    for source_data in sources.values():
        if not source_data:
            continue
        # Support both 'genre' (string) and 'genres' (list) keys
        genre_val = source_data.get('genres') or source_data.get('genre')
        if genre_val is None:
            continue
        if isinstance(genre_val, list):
            for g in genre_val:
                mapped = map_genre_to_ydj(g)
                if mapped:
                    ydj_genres.append(mapped)
        else:
            mapped = map_genre_to_ydj(genre_val)
            if mapped:
                ydj_genres.append(mapped)

    if not ydj_genres:
        return {
            'year': consensus_year,
            'genre_primary': None,
            'genre_alternate': None,
            'confidence': 'low'
        }

    # Count occurrences and rank
    genre_counts = {}
    for g in ydj_genres:
        genre_counts[g] = genre_counts.get(g, 0) + 1

    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)

    primary = sorted_genres[0][0]
    alternate = sorted_genres[1][0] if len(sorted_genres) > 1 else None

    if sorted_genres[0][1] >= 3:
        confidence = 'high'
    elif sorted_genres[0][1] >= 2:
        confidence = 'medium'
    else:
        confidence = 'low'

    return {
        'year': consensus_year,
        'genre_primary': primary,
        'genre_alternate': alternate,
        'confidence': confidence
    }
