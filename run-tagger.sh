#!/usr/bin/env bash
# Interactive batch tagger for Apple Music metadata.
# Reads recommendations from /tmp/recommendations.json and presents
# each track for single-keypress tagging (1=primary, 2=alternate, S=skip).
#
# Usage (from project root):
#   ./run-tagger.sh
#   ./run-tagger.sh --dry-run
#   ./run-tagger.sh --input /path/to/other.json

cd "$(dirname "$0")/library-management" || exit 1
python3 tag_tracks.py --input /tmp/recommendations.json "$@"
