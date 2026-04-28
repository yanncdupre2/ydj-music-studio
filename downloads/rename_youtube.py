#!/usr/bin/env python3
"""Rename YouTube-downloaded .mp4 files to a consistent format.

Uses the Apple Music library artist list to disambiguate artist vs. title
when YouTube titles are inconsistently ordered.

Output format:
    Artist - Title (Video).mp4          # for music videos
    Artist - Title (Karaoke).mp4        # for karaoke tracks
    Artist ft. Guest - Title (Remix).mp4  # featuring + remix preserved

Usage:
    python rename_youtube.py                     # dry-run (shows proposed renames)
    python rename_youtube.py --apply             # actually rename files
    python rename_youtube.py --dir /some/path    # use a different folder
"""

import argparse
import os
import re
import sys
import unicodedata

# ---------------------------------------------------------------------------
# Add project root so we can import common modules
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_DIR = os.path.expanduser("~/Movies/YouTube Downloads")

# Patterns considered "video" tags — removed from title, replaced with (Video)
VIDEO_TAGS = re.compile(
    r'\s*[\(\[]\s*'
    r'(?:Official\s+)?'
    r'(?:Music\s+)?'
    r'(?:Video|Clip\s+Officiel|Official\s+Video|Official\s+Music\s+Video)'
    r'(?:\s+\d+[Kk])?'  # e.g., "4K"
    r'\s*[\)\]]',
    re.IGNORECASE,
)

# Also catch "| Music Video" at end of title (no parens)
TRAILING_VIDEO_RE = re.compile(
    r'\s*\|\s*(?:Music\s+)?Video\s*$',
    re.IGNORECASE,
)

# Lyrics video patterns — detected before stripping noise tags
LYRICS_VIDEO_TAGS = re.compile(
    r'\s*[\(\[]\s*'
    r'(?:Lyrics?|Official\s+Lyric\s+Video|Lyric\s+Video|Paroles)'
    r'\s*[\)\]]',
    re.IGNORECASE,
)
# Also catch bare "Lyrics" or "Paroles" as a standalone word (not in parens)
LYRICS_BARE_RE = re.compile(
    r'(?:^|\s)[\-–—]\s*(?:Lyrics|Paroles)(?:\s|$)',
    re.IGNORECASE,
)

# Karaoke indicators anywhere in the filename
KARAOKE_RE = re.compile(r'karaok[eé]', re.IGNORECASE)

# Featuring patterns — both inline and parenthesized
FEAT_PAREN_RE = re.compile(
    r'\s*[\(\[]\s*(?:feat\.?|ft\.?|featuring)\s+(.+?)\s*[\)\]]',
    re.IGNORECASE,
)
FEAT_INLINE_RE = re.compile(
    r'\s+(?:feat\.?|ft\.?|featuring)\s+(.+)',
    re.IGNORECASE,
)

# Common "noise" parenthetical tags to strip
NOISE_TAGS = re.compile(
    r'\s*[\(\[]\s*(?:'
    r'Official\s+Audio'
    r'|Audio'
    r'|Visuali[sz]er'
    r'|Karaoke\s+Version'
    r'|Karaoke\s+Songs?\s+With\s+Lyrics[^)\]]*'
    r'|Karaoke\s+Instrumental[^)\]]*'
    r'|Karaoke'
    r'|Karaoké'
    r'|from\s+[^)\]]+?'
    r'|album\s+out\s+now'
    r'|Paroles[^)\]]*'
    r'|Création[^)\]]*'
    r')\s*[\)\]]',
    re.IGNORECASE,
)

# Fullwidth unicode characters YouTube uses in filenames
FULLWIDTH_MAP = {
    '\uff1a': ' -',  # ： → " -" (often used as separator)
    '\uff5c': '|',   # ｜
    '\uff02': '',     # ＂ → strip (decorative quotes)
    '\u2013': '-',    # –
    '\u2014': '-',    # —
}

# Separator between artist and title: " - ", " -- ", " – ", " — "
DASH_SEP_RE = re.compile(r'\s+[-–—]{1,2}\s+')

# Multiple spaces
MULTI_SPACE_RE = re.compile(r'\s{2,}')

# Characters not allowed in macOS filenames (or that cause trouble)
BAD_CHARS_RE = re.compile(r'[/:"|\[\]]')

# Common English words that happen to be short artist names — skip for substring matching
# (they're fine for exact whole-string matching)
AMBIGUOUS_SHORT_ARTISTS = {
    'all', 'air', 'boy', 'red', 'yes', 'lit', 'jet', 'era', 'x', 'm',
}


def normalize_for_matching(text):
    """Lowercase, strip accents, collapse whitespace — for fuzzy matching only."""
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = MULTI_SPACE_RE.sub(' ', text)
    return text


def build_artist_set():
    """Load all known artist names from Apple Music library CSV."""
    csv_path = os.path.join(PROJECT_ROOT, 'data', 'cleaned_music_library.csv')
    df = pd.read_csv(csv_path)
    artists = set()
    for col in ['Artist', 'Album Artist']:
        if col not in df.columns:
            continue
        for val in df[col].dropna().unique():
            val = val.strip()
            if val and val != 'Various Artists':
                artists.add(val)
    # Build a lookup: normalized -> original (prefer longer names)
    lookup = {}
    for a in artists:
        key = normalize_for_matching(a)
        if key not in lookup or len(a) > len(lookup[key]):
            lookup[key] = a
    return lookup


def replace_fullwidth(text):
    """Replace fullwidth Unicode chars with ASCII equivalents."""
    for fw, ascii_char in FULLWIDTH_MAP.items():
        text = text.replace(fw, ascii_char)
    return text


def sanitize_filename(name):
    """Remove characters that are problematic in filenames."""
    name = BAD_CHARS_RE.sub('', name)
    name = MULTI_SPACE_RE.sub(' ', name)
    return name.strip()


def extract_feat(text):
    """Extract featuring artist(s) from text, return (cleaned_text, feat_artists_str or None)."""
    feats = []

    # Parenthesized feat
    for m in FEAT_PAREN_RE.finditer(text):
        feats.append(m.group(1).strip())
    text = FEAT_PAREN_RE.sub('', text)

    # Inline feat (at end of string)
    m = FEAT_INLINE_RE.search(text)
    if m:
        feats.append(m.group(1).strip())
        text = text[:m.start()]

    feat_str = ', '.join(feats) if feats else None
    return text.strip(), feat_str


def try_exact_artist_match(text, artist_lookup):
    """Check if the entire text matches a known artist (normalized). Returns original-case name or None."""
    norm = normalize_for_matching(text)
    return artist_lookup.get(norm)


def find_artist_in_text(text, artist_lookup):
    """Try to find a known artist name as a substring of the given text.

    Returns (artist_as_it_appears_in_text, remaining_text) or (None, text).
    Tries longest matches first. Skips ambiguous short names.
    """
    text_norm = normalize_for_matching(text)

    # Sort candidates by length descending so longer matches win
    candidates = sorted(artist_lookup.items(), key=lambda kv: len(kv[0]), reverse=True)

    for norm_artist, original_artist in candidates:
        # Skip very short names and ambiguous common words for substring matching
        if len(norm_artist) < 3:
            continue
        if norm_artist in AMBIGUOUS_SHORT_ARTISTS:
            continue

        idx = text_norm.find(norm_artist)
        if idx == -1:
            continue

        # Word boundary check
        before = text_norm[idx - 1] if idx > 0 else ' '
        after_idx = idx + len(norm_artist)
        after = text_norm[after_idx] if after_idx < len(text_norm) else ' '
        if before.isalnum() or after.isalnum():
            continue

        # Use the text as it appeared in the filename (preserve original case)
        artist_as_in_file = text[idx:idx + len(norm_artist)].strip()
        remaining = text[:idx] + text[idx + len(norm_artist):]
        # Clean up leftover separators
        remaining = re.sub(r'^[\s\-–—:,]+', '', remaining)
        remaining = re.sub(r'[\s\-–—:,]+$', '', remaining)
        remaining = MULTI_SPACE_RE.sub(' ', remaining).strip()
        return artist_as_in_file, remaining

    return None, text


def strip_at_handle(text):
    """Remove @Handle prefix (e.g., '@VIZEofficial  x ') before artist name."""
    return re.sub(r'^@\S+\s+(?:x\s+)?', '', text).strip()


# Tags that are our own output format — not "raw" YouTube tags
OUR_OUTPUT_TAGS = re.compile(
    r'\((?:Video|Karaoke|Lyrics Video)\)$'
)


def _has_raw_tags(stem):
    """Check if a filename contains unprocessed YouTube tags that need normalization.

    Our own output tags like (Video), (Karaoke), (Lyrics Video) don't count.
    """
    # Strip our own output tags before checking
    cleaned = OUR_OUTPUT_TAGS.sub('', stem).strip()
    return bool(
        VIDEO_TAGS.search(cleaned)
        or TRAILING_VIDEO_RE.search(cleaned)
        or KARAOKE_RE.search(cleaned)
        or LYRICS_VIDEO_TAGS.search(cleaned)
        or LYRICS_BARE_RE.search(cleaned)
        or NOISE_TAGS.search(cleaned)
        or any(fw in cleaned for fw in FULLWIDTH_MAP)
    )


def already_well_formed(stem):
    """Check if a filename already matches our output format.

    Matches: Artist - Title, Artist ft. X - Title, with optional trailing (Tag).
    """
    # Pattern: something - something, optionally with ft. before the dash,
    # and optionally ending with (Tag)
    return bool(re.match(
        r'^.+?(?:\s+ft\.\s+.+?)?\s+-\s+.+?'
        r'(?:\s+\([^)]+\))*$',
        stem,
    ))


def classify_and_parse(stem, artist_lookup):
    """Parse a YouTube filename stem into (artist, title, suffix, feat).

    suffix is one of: '(Video)', '(Karaoke)', '(Lyrics Video)', or a preserved tag.
    """
    name = replace_fullwidth(stem)

    # Determine type (order matters: karaoke > lyrics > video)
    is_karaoke = bool(KARAOKE_RE.search(name))
    is_lyrics = bool(LYRICS_VIDEO_TAGS.search(name)) or bool(LYRICS_BARE_RE.search(name))
    is_video = bool(VIDEO_TAGS.search(name)) or bool(TRAILING_VIDEO_RE.search(name))

    # Strip video tags (both parenthesized and trailing)
    name = VIDEO_TAGS.sub('', name)
    name = TRAILING_VIDEO_RE.sub('', name)

    # Strip lyrics tags
    name = LYRICS_VIDEO_TAGS.sub('', name)
    name = LYRICS_BARE_RE.sub(' ', name)

    # Strip noise tags
    name = NOISE_TAGS.sub('', name)

    # Strip karaoke-specific leading words like "Karaoké" before artist
    name = re.sub(r'^Karaok[eé]\s+', '', name, flags=re.IGNORECASE)

    # Strip @ handles
    name = strip_at_handle(name)

    # Extract featuring artists
    name, feat = extract_feat(name)

    # Collect preserved parenthetical tags (remix, remaster, etc.)
    preserved_tags = []
    def collect_tag(m):
        preserved_tags.append(m.group(0).strip())
        return ''
    name = re.sub(
        r'\s*[\(\[]([^)\]]*(?:remix|remaster(?:ed)?|mix|edit|re-remix|filtered|instrumental|version|som original|visuali[sz]er)[^)\]]*)[\)\]]',
        collect_tag, name, flags=re.IGNORECASE,
    )

    # Clean up
    name = MULTI_SPACE_RE.sub(' ', name).strip()
    # Strip trailing pipes, dashes, etc.
    name = re.sub(r'[\s|:,\-–—]+$', '', name).strip()

    # Try splitting on dash separator
    parts = DASH_SEP_RE.split(name, maxsplit=1)

    artist = None
    title = None

    if len(parts) >= 2:
        # Could have more than 2 parts if there are multiple " - " separators
        # Re-split to get all parts
        all_parts = DASH_SEP_RE.split(name)

        if len(all_parts) == 2:
            left, right = all_parts[0].strip(), all_parts[1].strip()
            artist, title = _resolve_artist_title(left, right, artist_lookup)
        else:
            # Multiple dash-separated segments — try each split point
            # Prefer the one where the left side matches an artist
            best_artist = None
            best_title = None
            for i in range(1, len(all_parts)):
                left = ' - '.join(all_parts[:i]).strip()
                right = ' - '.join(all_parts[i:]).strip()
                a, t = _resolve_artist_title(left, right, artist_lookup)
                if a and try_exact_artist_match(a, artist_lookup):
                    best_artist, best_title = a, t
                    break
                if a and not best_artist:
                    best_artist, best_title = a, t
            if best_artist:
                artist, title = best_artist, best_title
            else:
                # Default: first part is artist, rest is title
                artist = all_parts[0].strip()
                title = ' - '.join(all_parts[1:]).strip()
    else:
        # No dash separator — try to find an artist in the whole string
        found_artist, remaining = find_artist_in_text(name, artist_lookup)
        if found_artist:
            artist = found_artist
            title = remaining if remaining else name
        else:
            artist = None
            title = name

    # Clean up title
    if title:
        title = re.sub(r'^[\s\-–—:,|]+', '', title)
        title = re.sub(r'[\s\-–—:,|]+$', '', title)
        title = MULTI_SPACE_RE.sub(' ', title).strip()

    # Clean up artist
    if artist:
        artist = re.sub(r'[\s\-–—:,|]+$', '', artist).strip()

    # Build suffix
    suffix_parts = []
    if preserved_tags:
        suffix_parts.extend(preserved_tags)
    if is_karaoke:
        suffix_parts.append('(Karaoke)')
    elif is_lyrics:
        suffix_parts.append('(Lyrics Video)')
    elif is_video:
        suffix_parts.append('(Video)')

    suffix = ' '.join(suffix_parts) if suffix_parts else None

    return artist, title, suffix, feat


def _resolve_artist_title(left, right, artist_lookup):
    """Given two parts split by ' - ', figure out which is artist and which is title."""
    # 1. Exact match: left is a known artist
    if try_exact_artist_match(left, artist_lookup):
        return left, right

    # 2. Exact match: right is a known artist (title-first format)
    if try_exact_artist_match(right, artist_lookup):
        return right, left

    # 3. Substring match: find an artist in the left part
    found, remaining = find_artist_in_text(left, artist_lookup)
    if found:
        # If there's remaining text on the left, the whole left is likely a multi-artist string
        return left, right

    # 4. Substring match: find an artist in the right part
    found, remaining = find_artist_in_text(right, artist_lookup)
    if found:
        return right, left

    # 5. Default: left is artist, right is title
    return left, right


def build_new_name(artist, title, suffix, feat):
    """Assemble the final filename (without extension)."""
    parts = []
    if artist:
        if feat:
            parts.append(f"{artist} ft. {feat} - {title}")
        else:
            parts.append(f"{artist} - {title}")
    else:
        if feat:
            parts.append(f"{title} ft. {feat}")
        else:
            parts.append(title)

    if suffix:
        parts.append(suffix)

    return sanitize_filename(' '.join(parts))


def main():
    parser = argparse.ArgumentParser(description='Rename YouTube downloads to consistent format.')
    parser.add_argument('--dir', default=DEFAULT_DIR, help='Directory with .mp4 files')
    parser.add_argument('--apply', action='store_true', help='Actually rename (default is dry-run)')
    args = parser.parse_args()

    directory = os.path.expanduser(args.dir)
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory")
        sys.exit(1)

    print("Loading Apple Music library for artist matching...")
    artist_lookup = build_artist_set()
    print(f"Loaded {len(artist_lookup)} unique artist names.\n")

    files = sorted(f for f in os.listdir(directory) if f.lower().endswith('.mp4'))
    if not files:
        print("No .mp4 files found.")
        return

    renames = []
    skipped = []
    unmatched = []

    # First pass: compute desired names and count conflicts
    parsed = []  # list of (fname, new_name, new_stem, artist)
    target_counts = {}
    for fname in files:
        stem = fname[:-4]

        # Skip re-parsing files that are already well-formed and have no raw tags to normalize
        if already_well_formed(stem) and not _has_raw_tags(stem):
            parsed.append((fname, fname, stem, 'SKIP'))
            key = fname.lower()
            target_counts[key] = target_counts.get(key, 0) + 1
            continue

        artist, title, suffix, feat = classify_and_parse(stem, artist_lookup)
        new_stem = build_new_name(artist, title, suffix, feat)
        new_name = new_stem + '.mp4'
        key = new_name.lower()
        target_counts[key] = target_counts.get(key, 0) + 1
        parsed.append((fname, new_name, new_stem, artist))

    # Second pass: assign indexed names where there are conflicts
    target_seen = {}
    for fname, new_name, new_stem, artist in parsed:
        if artist == 'SKIP':
            skipped.append(fname)
            continue

        key = new_name.lower()

        # If multiple files map to the same name, add an index
        if target_counts[key] > 1:
            idx = target_seen.get(key, 0) + 1
            target_seen[key] = idx
            if idx > 1:
                new_name = f"{new_stem} ({idx}).mp4"
        # Also check if target already exists on disk (from a file not being renamed)
        elif os.path.exists(os.path.join(directory, new_name)) and new_name != fname:
            # Find next available index
            idx = 2
            while os.path.exists(os.path.join(directory, f"{new_stem} ({idx}).mp4")):
                idx += 1
            new_name = f"{new_stem} ({idx}).mp4"

        if new_name == fname:
            skipped.append(fname)
            continue

        if artist is None:
            unmatched.append((fname, new_name))
        else:
            renames.append((fname, new_name))

    # Display results
    if renames:
        print(f"=== Proposed renames ({len(renames)}) ===\n")
        for old, new in renames:
            print(f"  {old}")
            print(f"    -> {new}\n")

    if unmatched:
        print(f"=== No artist detected ({len(unmatched)}) — please review ===\n")
        for old, new in unmatched:
            print(f"  {old}")
            print(f"    -> {new}\n")

    if skipped:
        print(f"=== Already correct ({len(skipped)}) ===\n")
        for s in skipped:
            print(f"  {s}")
        print()

    # Apply
    if args.apply and (renames or unmatched):
        all_renames = renames + unmatched
        print(f"Renaming {len(all_renames)} file(s)...")
        errors = 0
        for old, new in all_renames:
            old_path = os.path.join(directory, old)
            new_path = os.path.join(directory, new)
            try:
                os.rename(old_path, new_path)
                print(f"  OK: {new}")
            except OSError as e:
                print(f"  ERROR: {old} -> {new}: {e}")
                errors += 1
        print(f"\nDone! ({len(all_renames) - errors} renamed, {errors} errors)")
    elif not args.apply and (renames or unmatched):
        print("Dry run — use --apply to rename files.")


if __name__ == '__main__':
    main()
