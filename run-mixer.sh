#!/usr/bin/env bash
# run-mixer.sh — activate venv and run the YDJ Mixer optimizer
#
# Usage:
#   ./run-mixer.sh           # default 5 min budget
#   ./run-mixer.sh 2         # 2 min budget
#   ./run-mixer.sh 0.5       # 30 second budget (quick test)

set -e
cd "$(dirname "$0")"
source venv/bin/activate
python3 mixer/mixer.py "$@"
