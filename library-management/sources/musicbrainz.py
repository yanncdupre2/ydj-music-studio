#!/usr/bin/env python3
"""Source D: MusicBrainz API lookup.

Queries MusicBrainz for recording metadata (year, genres/tags).
Strips "(Video)" / "(Lyric Video)" suffixes before querying to improve hit rate.

CLI:  python3 sources/musicbrainz.py "Artist" "Title"
Import: from sources.musicbrainz import get_musicbrainz
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request


def strip_video_suffix(title):
    """Remove (Video), (Lyric Video), (Official Video) etc. from title."""
    return re.sub(r'\s*\((?:Official\s+)?(?:Lyric\s+)?Video\)', '', title, flags=re.IGNORECASE).strip()


def get_musicbrainz(artist, title):
    """Query MusicBrainz API for a recording.

    Returns dict with keys: year, genres, score — or None if no results.
    Returns dict with 'error' key on failure.
    """
    clean_title = strip_video_suffix(title)

    headers = {
        'User-Agent': 'YDJMusicStudio/1.0 (https://github.com/yanncdupre2/ydj-music-studio)'
    }

    query = f'artist:"{artist}" AND recording:"{clean_title}"'
    url = f'https://musicbrainz.org/ws/2/recording/?query={urllib.parse.quote(query)}&fmt=json&limit=3'

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        time.sleep(1.0)  # MusicBrainz rate limit: 1 req/sec

        recordings = data.get('recordings', [])
        if not recordings:
            return None

        recording = recordings[0]

        year = None
        if 'releases' in recording and recording['releases']:
            release = recording['releases'][0]
            date_str = release.get('date', '')
            if date_str:
                year = int(date_str.split('-')[0])

        genres = [tag['name'] for tag in recording.get('tags', []) if tag.get('count', 0) > 0]

        return {
            'year': year,
            'genres': genres,
            'score': recording.get('score', 0)
        }

    except Exception as e:
        return {'error': str(e)}


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 sources/musicbrainz.py <artist> <title>")
        sys.exit(1)

    artist = sys.argv[1]
    title = sys.argv[2]

    result = get_musicbrainz(artist, title)
    print(json.dumps(result, indent=2))
