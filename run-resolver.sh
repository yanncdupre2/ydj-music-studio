#!/usr/bin/env bash
# Interactive inconsistency resolver for Apple Music metadata.
# Must run in Terminal (needs interactive TTY for single-keypress input).
#
# Usage (from project root):
#   ./run-resolver.sh
#   ./run-resolver.sh --dry-run

cd "$(dirname "$0")/library-management" || exit 1
python3 resolve_tagger.py --input /tmp/inconsistency_groups.json "$@"
